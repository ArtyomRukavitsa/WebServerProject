from flask import Flask, render_template, redirect, abort, request, make_response, jsonify
from data import db_session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_restful import reqparse, abort, Api, Resource
from forms import RegisterForm, LoginForm, BooksForm, AuthorForm, InputForm, GenreForm
import wikipedia
from data.users import User
from data.books import Books
from data.author import Author
from data.genres import Genre
from data.users_recource import UsersListResource, UsersResource
from data.books_resource import BooksResource, BooksListResource
from data.author_resource import AuthorsResource, AuthorsListResource
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = 'WEB_SERVER_project'
login_manager = LoginManager()
login_manager.init_app(app)
api = Api(app)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


# Главная: обдумать, что будет!
@app.route('/', methods=['GET', 'POST'])
@app.route('/main', methods=['GET', 'POST'])
def index():
    form = InputForm()
    if form.validate_on_submit():
        message = form.message.data
        answer = request.form['req']
        return sent(message, answer)
    return render_template("main.html", title='Главная', form=form, warning='')


@login_required
def sent(message, answer):
    answers = ['Вывод пользователей (введите users)', 'Книга(введите название)', 'Автор(введите имя и фамилию)']
    a = answers.index(answer)
    print(message, answer)
    form = InputForm()
    if a == 0:
        if current_user.id == 1:
            return redirect('/request/users')
        else:
            return render_template("main.html", title='Главная', form=form, warning='Недостаточно прав')
    elif a == 1:
        session = db_session.create_session()
        book = session.query(Books).filter(Books.title == message).first()
        author = session.query(Author).filter(Author.id == book.author_id).first()
        b = "_".join(book.title.strip().split())
        url = f'https://ru.wikipedia.org/wiki/{b}'
        return render_template('books.html', books=[book], names=[author.name],
                               surnames=[author.surname], extra_info=[url])
    elif a == 2:
        session = db_session.create_session()
        name, surname = message.split()
        author = session.query(Author).filter(Author.name == name, Author.surname == surname).first()
        url = f'https://ru.wikipedia.org/wiki/{author.name} {author.surname}'
        return render_template('authors.html', authors=[author], extra_info=[url])


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/request/users')
@login_required
def users():
    session = db_session.create_session()
    users = session.query(User).all()
    return render_template('users.html', users=users)


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
    session = db_session.create_session()
    user = session.query(User).get(current_user.id)
    user.bought = ''
    session.commit()
    logout_user()
    return redirect("/")


# Отображение всех писателей
@app.route('/authors')
def authors():
    session = db_session.create_session()
    authors = session.query(Author).all()
    extra_info = []
    for author in authors:
        url = f'https://ru.wikipedia.org/wiki/{author.name} {author.surname}'
        extra_info.append(url)
    return render_template('authors.html', authors=authors, extra_info=extra_info)


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


@app.route('/genres')
def genres():
    session = db_session.create_session()
    genres = session.query(Genre).all()
    extra_info = []
    for genre in genres:
        url = f'https://ru.wikipedia.org/wiki/{genre.genre}'
        extra_info.append(url)
    return render_template('genres.html', genres=genres, extra_info=extra_info)


# Добавление писателя (только админ)
@app.route('/addgenres', methods=['GET', 'POST'])
@login_required
def addgenre():
    form = GenreForm()
    session = db_session.create_session()
    if form.validate_on_submit():
        if session:
            genre = Genre(
            genre=form.genre.data
            )
            session.add(genre)
            session.commit()
            return redirect("/")
        return redirect('/logout')
    return render_template('addgenre.html', title='Добавление жанра', form=form)


@app.route('/genres_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def genre_delete(id):
    session = db_session.create_session()
    genre = session.query(Genre).filter(Genre.id == id,
                                   current_user.id == 1).first()
    if genre:
        session.delete(genre)
        session.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/genres/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_authors(id):
    form = GenreForm()
    if request.method == "GET":
        session = db_session.create_session()
        genre = session.query(Genre).filter(Genre.id == id,
                                          current_user.id == 1).first()
        if genre:
            form.genre.data = genre.genre
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        genre = session.query(Genre).filter(Genre.id == id,
                                            current_user.id == 1).first()
        if genre:
            genre.genre = form.genre.data
            session.commit()
            return redirect('/genres')
        else:
            abort(404)
    return render_template('addgenre.html', title='Редактирование жанров', form=form)

# Отображение всех книг
@app.route('/books')
def books():
    session = db_session.create_session()
    books = session.query(Books).all()
    names, surnames, genres, extra_info = [], [], [], []
    for book in session.query(Books).all():
        author = session.query(Author).filter(Author.id == book.author_id).first()
        genres = session.query(Genre).filter(Genre.id == book.genre_id).first()
        names.append(author.name)
        surnames.append(author.surname)
        b = "_".join(book.title.strip().split())
        url = f'https://ru.wikipedia.org/wiki/{b}'
        extra_info.append(url)
    return render_template('books.html', books=books, names=names, surnames=surnames,
                           extra_info=extra_info, genres=genres)


# Обрабочик кнопки "Купить книгу"
@app.route('/books_buy/<int:book_id>')
@login_required
def books_buy(book_id):
    session = db_session.create_session()
    user = session.query(User).get(current_user.id)
    if not user.bought:  # пользователь за сессию не положил в корзину ни одной книги
        user.bought = ''
    user.bought += str(book_id) + ', '
    session.commit()
    return redirect('/books')


# Обрабочик Корзины
@app.route('/basket')
@login_required
def basket():
    session = db_session.create_session()
    user = session.query(User).get(current_user.id)
    books_id = user.bought.strip(', ')
    names, surnames, books = [], [], []
    cost = 0
    if books_id:
        for id in books_id.split(','):
            book = session.query(Books).filter(Books.id == id).first()
            author = session.query(Author).filter(Author.id == book.author_id).first()
            names.append(author.name)
            surnames.append(author.surname)
            books.append(book)
            cost += book.price
    return render_template('basket.html', title='Корзина', books=books, names=names, surnames=surnames, cost=cost)


# Обрабочик кнопки "Купить книгу"
@app.route('/buy')
@login_required
def buy():
    session = db_session.create_session()
    user = session.query(User).get(current_user.id)
    books_id = user.bought.strip(', ').split(',')
    cost = 0
    for id in books_id:
        book = session.query(Books).filter(Books.id == id).first()
        cost += book.price
    if not user.total_sum:
        user.total_sum = 0
    user.total_sum += cost  # установка значения в колонку с общими затратами
    user.bought = ''  # купленных книг в этой сессии уже нет
    session.commit()
    return redirect('/books')



@app.route('/books_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def books_delete(id):
    session = db_session.create_session()
    books = session.query(Books).filter(Books.id == id,
                                   current_user.id == 1).first()
    if books:
        session.delete(books)
        session.commit()
        os.remove(f'static/img/book{books.id}.jpg')
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
    genre = session.query(Genre)
    if form.validate_on_submit():
        if session:
            book = Books(
            author_id=author.filter(Author.surname == form.author.data).first().id,
            genre_id=genre.filter(Genre.genre == form.genre.data).first().id,
            title=form.title.data,
            date=form.date.data,
            price=form.price.data
            )
            book.cover = 'string'  # заглушка
            # Идея: создаю новую книгу, но заранее мне неизвестен ее id для корректного названия книги
            session.add(book)
            session.commit()
            book = session.query(Books).filter(Books.title == form.title.data).first()
            photo = f"book{book.id}.jpg"
            f = request.files['file']
            with open(photo, "wb") as file:
                file.write(f.read())
            book.cover = photo
            session.commit()
            return redirect("/")
        return redirect('/logout')
    return render_template('addbooks.html', title='Добавление книги', form=form)


@app.route('/books/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    form = BooksForm()
    if request.method == "GET":
        session = db_session.create_session()
        book = session.query(Books).filter(Books.id == id,
                                          current_user.id == 1).first()
        if book:
            author = session.query(Author).filter(Author.id == book.author_id).first()
            genre = session.query(Genre).filter(Genre.id == book.genre_id).first()
            form.author.data = author.surname
            form.title.data = book.title
            form.genre.data = genre.genre
            form.date.data = book.date
            form.cover.data = book.cover
            form.price.data = book.price
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        book = session.query(Books).filter(Books.id == id,
                                           current_user.id == 1).first()
        if book:
            author = session.query(Author).filter(Author.surname == form.author.data).first()
            genre = session.query(Genre).filter(Genre.genre == form.genre.data).first()
            book.author_id = author.id
            book.genre_id = genre.id
            book.title = form.title.data
            book.date = form.date.data
            book.price = form.price.data
            book.cover = form.cover.data
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('addbooks.html', title='Редактирование книги', form=form)


# Запуск программы
def main():
    db_session.global_init("db/book_shop.sqlite")
    api.add_resource(UsersListResource, '/api/v1/users')
    api.add_resource(UsersResource, '/api/v1/users/<int:user_id>')
    api.add_resource(BooksListResource, '/api/v1/books')
    api.add_resource(BooksResource, '/api/v1/books/<int:books_id>')
    api.add_resource(AuthorsListResource, '/api/v1/author')
    api.add_resource(AuthorsResource, '/api/v1/books/<int:author_id>')
    app.run()


if __name__ == '__main__':
    main()
