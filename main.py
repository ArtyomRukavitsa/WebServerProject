from flask import Flask, render_template, redirect, abort, request
from data import db_session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from forms import RegisterForm, LoginForm, BooksForm, AuthorForm
from data.users import User
from data.books import Books
from data.author import Author


app = Flask(__name__)
app.config['SECRET_KEY'] = 'WEB_SERVER_project'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


# Главная: обдумать, что будет!
@app.route('/')
@app.route('/main')
def index():
    return render_template("main.html", title='Главная')


# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            surname=form.surname.data,
            nickname=form.nickname.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
        # return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)


# Страница авторизации
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# Отображение всех писателей
@app.route('/authors')
def authors():
    session = db_session.create_session()
    author = session.query(Author)
    return render_template('authors.html', authors=author)


# Добавление писателя (только админ)
@app.route('/addauthor', methods=['GET', 'POST'])
@login_required
def addauthor():
    form = AuthorForm()
    session = db_session.create_session()
    if form.validate_on_submit():
        if session:
            author = Author(
            name=form.name.data,
            surname=form.surname.data,
            years=form.years.data,
            list_of_books=form.list_of_books.data
            )
            session.add(author)
            session.commit()
            return redirect("/")
        return redirect('/logout')
    return render_template('addauthor.html', title='Добавление писателя', form=form)

@app.route('/author_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def author_delete(id):
    session = db_session.create_session()
    author = session.query(Author).filter(Author.id == id,
                                   current_user.id == 1).first()
    if author:
        session.delete(author)
        session.commit()
    else:
        abort(404)
    return redirect('/')


# Отображение всех книг
@app.route('/books')
def books():
    session = db_session.create_session()
    books = session.query(Books).all()
    author = session.query(Author)
    return render_template('books.html', books=books, author=author)


@app.route('/books_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def books_delete(id):
    session = db_session.create_session()
    books = session.query(Books).filter(Books.id == id,
                                   current_user.id == 1).first()
    if books:
        session.delete(books)
        session.commit()
    else:
        abort(404)
    return redirect('/')


# Добавление книги (только админ)
@app.route('/addbooks', methods=['GET', 'POST'])
@login_required
def addbooks():
    form = BooksForm()
    session = db_session.create_session()
    author = session.query(Author)
    if form.validate_on_submit():
        if session:
            book = Books(
            author_id=author.filter(Author.surname == form.author.data).first().id,
            title=form.title.data,
            cover=form.cover.data,
            date=form.date.data
            )
            session.add(book)
            session.commit()
            return redirect("/")
        return redirect('/logout')
    return render_template('addbooks.html', title='Добавление книги', form=form)


@app.route('/books/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_job(id):
    form = BooksForm()
    if request.method == "GET":
        session = db_session.create_session()
        book = session.query(Books).filter(Books.id == id,
                                          current_user.id == 1).first()
        if book:
            form.author.data = book.author
            form.title.data = book.title
            form.date.data = book.date
            form.cover.data = book.cover
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        book = session.query(Books).filter(Books.id == id,
                                          current_user.id == 1).first()
        if book:
            book.author = form.author.data
            book.title = form.title.data
            book.date = form.date.data
            book.cover = form.cover.data
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('addbook.html', title='Редактирование книги', form=form)


# Запуск программы
def main():
    db_session.global_init("db/book_shop.sqlite")
    app.run()


if __name__ == '__main__':
    main()