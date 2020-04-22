from flask import Flask, render_template, redirect, abort, request, make_response, jsonify
from data import db_session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_restful import reqparse, abort, Api, Resource
from forms import RegisterForm, LoginForm, BooksForm, AuthorForm, \
    InputForm, GenreForm, AuthorSearch, GenreSearch, PriceSearch, CreditCard, BookReview
import wikipediaapi
import requests
from data.users import User
from data.books import Books
from data.author import Author
from data.genres import Genre
import datetime
from data.card_algs import luhn_algorithm
import os
from data.auth_data import artem, natasha, project

app = Flask(__name__)
app.config['SECRET_KEY'] = 'WEB_SERVER_project'
login_manager = LoginManager()
login_manager.init_app(app)
api = Api(app)
wiki_wiki = wikipediaapi.Wikipedia('ru')


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
    form = InputForm()
    if a == 0:
        if current_user.id == 1:
            return redirect('/request/users')
        else:
            return render_template("main.html", title='Главная', form=form, warning='Недостаточно прав')
    elif a == 1:
        session = db_session.create_session()
        book = session.query(Books).filter(Books.title == message).first()
        if book:
            author = session.query(Author).filter(Author.id == book.author_id).first()
            genre = session.query(Genre).filter(Genre.id == book.genre_id).first().genre
            b = "_".join(book.title.strip().split())
            url = f'https://ru.wikipedia.org/wiki/{b}'
            return render_template('books.html', title='Книга', books=[book], names=[author.name],
                                   surnames=[author.surname], extra_info=[url], genres=[genre], err='')
        return render_template('books.html', title='Книга', err='Данной книги у нас нет в наличии')
    elif a == 2:
        session = db_session.create_session()
        name, surname = message.split()
        author = session.query(Author).filter(Author.name == name, Author.surname == surname).first()
        if author:
            url = f'https://ru.wikipedia.org/wiki/{author.name} {author.surname}'
            return render_template('authors.html', title='Автор', authors=[author], extra_info=[url], err='')
        return render_template('authors.html', title='Автор', err='Книг данного писателя у нас нет в наличии')


@app.route('/searchauthor', methods=['GET', 'POST'])
@login_required
def search_by_author():
    form = AuthorSearch()
    if form.validate_on_submit():
        surname = form.surname.data
        session = db_session.create_session()
        author = session.query(Author).filter(Author.surname == surname).first()
        if not author:
            return render_template('searchauthor.html', title='Фильтрация по автору', form=form, message='Книг такого автора у нас нет')
        books = session.query(Books).filter(Books.author_id == author.id).all()
        genres, url = [], []
        for book in books:
            genres.append(session.query(Genre).filter(Genre.id == book.genre_id).first().genre)
            b = "_".join(book.title.strip().split())
            url_ = f'https://ru.wikipedia.org/wiki/{b}'
            url.append(url_)
        return render_template('books.html', title='Фильтрация по автору', books=books,
                               surnames=[author.surname] * len(books), names=[author.name] * len(books),
                               genres=genres, extra_info=url, message='')
    return render_template("searchauthor.html", title='Фильтрация по автору', form=form, message='')


@app.route('/searchgenre', methods=['GET', 'POST'])
@login_required
def search_by_genre():
    form = GenreSearch()
    if form.validate_on_submit():
        genre = form.genre.data.lower()
        session = db_session.create_session()
        genre = session.query(Genre).filter(Genre.genre == genre).first()
        if not genre:
            return render_template('searchgenre.html', title='Фильтрация по жанру', form=form,
                                   message='Книг такого жанра у нас нет')
        books = session.query(Books).filter(Books.genre_id == genre.id).all()
        names, surnames, url = [], [], []
        for book in books:
            author = session.query(Author).filter(Author.id == book.author_id).first()
            names.append(author.name)
            surnames.append(author.surname)
            b = "_".join(book.title.strip().split())
            url_ = f'https://ru.wikipedia.org/wiki/{b}'
            url.append(url_)
        return render_template('books.html', title='Фильтрация по жанру', books=books,
                               surnames=surnames, names=names,
                               genres=[genre.genre] * len(books), extra_info=url, message='')
    return render_template("searchgenre.html", title='Фильтрация по жанру', form=form, message='')


@app.route('/searchprice', methods=['GET', 'POST'])
@login_required
def search_by_price():
    form = PriceSearch()
    if form.validate_on_submit():
        minimum = form.minimum.data
        maximum = form.maximum.data
        if minimum > maximum:
            return render_template('searchprice.html', title='Фильтрация по цене', form=form,
                                   message='Поле с минимальным значением хранит большее значение')
        session = db_session.create_session()
        books = session.query(Books).filter(Books.price >= minimum, Books.price <= maximum).all()
        if not books:
            return render_template('searchprice.html', title='Фильтрация по цене', form=form,
                                   message='Книг в такой ценовой категории у нас нет')
        names, surnames, url, genres = [], [], [], []
        for book in books:
            author = session.query(Author).filter(Author.id == book.author_id).first()
            genres.append(session.query(Genre).filter(Genre.id == book.genre_id).first().genre)
            names.append(author.name)
            surnames.append(author.surname)
            b = "_".join(book.title.strip().split())
            url_ = f'https://ru.wikipedia.org/wiki/{b}'
            url.append(url_)
        return render_template('books.html', title='Фильтрация по жанру', books=books,
                               surnames=surnames, names=names,
                               genres=genres, extra_info=url, message='')
    return render_template("searchprice.html", title='Фильтрация по жанру', form=form, message='')


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/request/users')
@login_required
def users():
    session = db_session.create_session()
    users = session.query(User).all()
    return render_template('users.html', title='Все пользователи', users=users)


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
                               title='Авторизация',
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


@app.route('/maps')
def maps():
    map_api_server = 'http://static-maps.yandex.ru/1.x/?37.620070,55.753630&size=450,450&spn=3.5,3.5&l=map'
    places = []
    session = db_session.create_session()
    authors = session.query(Author).all()
    extra_info = []
    for author in authors:
        page_py = wiki_wiki.page(f'{author.name}_{author.surname}')
        extra_info.append(page_py.fullurl)
        a = page_py.text.split()
        a = a[a.index("родился"): a.index("родился") + 10]
        a = a[a.index("в") + 1:]
        for i in a:
            if i[0].islower():
                continue
            i = i.replace(',', '')
            i = i.replace('.', '')
            i = i.replace('-', '')
            i = i.replace('—', '')

            geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

            geocoder_params = {
                "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
                "geocode": i,
                "format": "json"}

            response = requests.get(geocoder_api_server, params=geocoder_params)
            if response:
                # Преобразуем ответ в json-объект
                json_response = response.json()
                if len(json_response["response"]["GeoObjectCollection"]["featureMember"]) == 0:
                    continue
                # Получаем первый топоним из ответа геокодера.
                toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                toponym_coodrinates = toponym["Point"]["pos"].split()
                toponym_address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
                print(json_response)
                places.append(toponym_address)
                # Долгота и Широта :
                if 'pt' not in map_api_server:
                    map_api_server += f"&pt={toponym_coodrinates[0]},{toponym_coodrinates[1]},pm2rdm{author.id}"
                else:
                    map_api_server += f"~{toponym_coodrinates[0]},{toponym_coodrinates[1]},pm2rdm{author.id}"
                break
    return render_template('maps.html', title='Карта', authors=authors, api=map_api_server, place=places)

# Отображение всех писателей
@app.route('/authors')
def authors():
    session = db_session.create_session()
    authors = session.query(Author).all()
    extra_info = []
    for author in authors:
        page_py = wiki_wiki.page(f'{author.name}_{author.surname}')
        extra_info.append(page_py.fullurl)
        a = page_py.text.split()
    return render_template('authors.html', title='Все авторы', authors=authors, extra_info=extra_info)


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
        page_py = wiki_wiki.page(f'{genre.genre}')
        extra_info.append(page_py.fullurl)
    return render_template('genres.html', title='Все жанры', genres=genres, extra_info=extra_info)


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
        genre = session.query(Genre).filter(Genre.id == book.genre_id).first()
        genres.append(genre.genre)
        names.append(author.name)
        surnames.append(author.surname)
        b = "_".join(book.title.strip().split())

        page_py = wiki_wiki.page(f'{b}')
        extra_info.append(page_py.fullurl)

    return render_template('books.html', title='Все книги', books=books, names=names, surnames=surnames,
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


@app.route('/books_review/<int:book_id>', methods=["GET", "POST"])
@login_required
def books_review(book_id):
    form = BookReview()
    session = db_session.create_session()
    book = session.query(Books).get(book_id)
    if form.validate_on_submit():
        review = form.review.data
        if not book.review:
            book.review = ""
        book.review += f"{review}+"
        session.commit()
        return redirect('/books')

    return render_template('books_review.html', title='Оставить отзыв', book=book, form=form)


@app.route('/books_review_show/<int:book_id>', methods=["GET", "POST"])
@login_required
def books_review_show(book_id):
    session = db_session.create_session()
    book = session.query(Books).get(book_id)
    if book.review:
        reviews = book.review.strip('+').split('+')
        return render_template('books_review_show.html', title='Все отзывы о книге', book=book, reviews=reviews)
    return render_template('books_review_show.html', title='Все отзывы о книге',
                           book=book, err='Отзывов к этой книге пока нет!')


# Обрабочик Корзины
@app.route('/basket')
@login_required
def basket():
    session = db_session.create_session()
    user = session.query(User).get(current_user.id)
    books_id = user.bought
    names, surnames, books = [], [], []
    cost = 0
    if books_id:
        for id in books_id.strip(', ').split(','):
            book = session.query(Books).filter(Books.id == id).first()
            author = session.query(Author).filter(Author.id == book.author_id).first()
            names.append(author.name)
            surnames.append(author.surname)
            books.append(book)
            cost += book.price
        return render_template('basket.html', title='Корзина', books=books, names=names, surnames=surnames, cost=cost)
    return render_template('basket.html', title='Корзина', message='Ваша корзина пуста')


# Обрабочик Корзины
@app.route('/basket_delete/<int:number>')
@login_required
def basket_delete(number):
    session = db_session.create_session()
    user = session.query(User).get(current_user.id)
    books_id = user.bought
    books_id = books_id.strip(', ').split(',')
    books_id.remove(str(number))
    user.bought = ', '.join(books_id)
    session.commit()
    return redirect('/basket')

# Обрабочик псевдо-оплаты
@app.route('/credit_card', methods=['GET', 'POST'])
@login_required
def credit_card():
    form = CreditCard()
    session = db_session.create_session()
    if form.validate_on_submit():
        user = session.query(User).filter(User.surname == form.surname.data).first()
        if not user:
            return render_template('credit_card.html',
                                   title='Оплата покупок',
                                   message='Пользователя с данной фамилией не найдено',
                                   form=form)
        if user.name != form.name.data:
            return render_template('credit_card.html',
                                   title='Оплата покупок',
                                   message='Введенное имя не совпадает с именем, введенным при регистрации',
                                   form=form)
        card_number = "".join(form.card_number.data.strip().split())
        if not card_number.isdigit():
            return render_template('credit_card.html',
                                   title='Оплата покупок',
                                   message='В номере банковской карты присутствуют буквы или другие знаки!',
                                   form=form)
        if len(card_number) != 16:
            return render_template('credit_card.html',
                                   title='Оплата покупок',
                                   message='Длина банковской карты не составляет 16 цифр!',
                                   form=form)
        if not luhn_algorithm(card_number):
            return render_template('credit_card.html',
                                   title='Оплата покупок',
                                   message='Данного номера банковской карты не существует! Проверьте данные',
                                   form=form)
        try:
            month, year = form.month_year.data.split('/')
        except ValueError:
            return render_template('credit_card.html',
                                   title='Оплата покупок',
                                   message='Нарушение формата даты истечения срока карты!',
                                   form=form)
        if not month.isdigit() or not year.isdigit():
            return render_template('credit_card.html',
                                   title='Оплата покупок',
                                   message='Либо дата, либо год истечения срока '
                                           'карты содержит буквы или спец. символы',
                                   form=form)
        if int(month) > 12 or int(month) < 1:
            return render_template('credit_card.html',
                                   title='Оплата покупок',
                                   message='Число месяца может быть от 1 до 12!',
                                   form=form)
        if len(str(year)) != 2:
            return render_template('credit_card.html',
                                   title='Оплата покупок',
                                   message='Число года — двузначное число! Проверьте данные!',
                                   form=form)
        now = datetime.datetime.now()
        card_expiration = datetime.datetime(day=1, month=int(month), year=2000 + int(year))
        if now > card_expiration:
            return render_template('credit_card.html',
                                   title='Оплата покупок',
                                   message='Срок действия вашей банковской карты просрочен!',
                                   form=form)
        return redirect('/buy')
    return render_template('credit_card.html', title='Оплата покупок', message='', form=form)


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
            photo = f"static/img/book{book.id}.jpg"
            f = request.files['file']
            with open(photo, "wb") as file:
                file.write(f.read())
            book.cover = f'book{book.id}.jpg'
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


@app.route('/contacts')
def contacts():
    return render_template('contacts.html', title='Контакты', artem=artem, natasha=natasha, project=project)


# Запуск программы
def main():
    db_session.global_init("db/book_shop.sqlite")
    app.run()


if __name__ == '__main__':
    main()
