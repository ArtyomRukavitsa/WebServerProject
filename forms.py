from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, length


class RegisterForm(FlaskForm):
    name = StringField('Имя пользователя', validators=[DataRequired()])
    surname = StringField('Фамилия пользователя', validators=[DataRequired()])
    nickname = StringField('Nick пользователя на сайте', validators=[DataRequired()])
    email = StringField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Регистрация')


class LoginForm(FlaskForm):
    email = StringField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class BooksForm(FlaskForm):
    author = StringField('Фамилия автора', validators=[DataRequired()])
    title = StringField('Название книги', validators=[DataRequired()])
    genre = StringField('Название жанра')
    date = IntegerField('Дата создания книги', validators=[DataRequired()])
    price = IntegerField('Цена книги', validators=[DataRequired()])
    cover = StringField('Обложка книги')
    submit = SubmitField('Добавить книгу')


class AuthorForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    years = StringField('Годы жизни (в формате YEAR-YEAR)')
    list_of_books = StringField('Список сочиненных книг')
    submit = SubmitField('Добавить автора')


class InputForm(FlaskForm):
    message = StringField('')


class GenreForm(FlaskForm):
    genre = StringField('Название жанра', validators=[DataRequired()])


class AuthorSearch(FlaskForm):
    surname = StringField('Фамилия писателя', validators=[DataRequired()])


class GenreSearch(FlaskForm):
    genre = StringField('Жанр книг', validators=[DataRequired()])


class PriceSearch(FlaskForm):
    minimum = IntegerField('Минимальная цена книги', validators=[DataRequired()])
    maximum = IntegerField('Максимальная цена книги', validators=[DataRequired()])
    submit = SubmitField('Поиск')


class CreditCard(FlaskForm):
    name = StringField('Ваше имя', validators=[DataRequired()])
    surname = StringField('Ваша фамилия', validators=[DataRequired()])
    card_number = StringField('Ваша банковская карта (формат: XXXX XXXX XXXX XXXX)', validators=[DataRequired()])
    month_year = StringField('Месяц и год истечения карты (формат: ММ/ГГ)')
    submit = SubmitField('Оплатить')


class BookReview(FlaskForm):
    review = TextAreaField('Напишите отзыв к книге!', validators=[DataRequired(), length(max=200)])
    submit = SubmitField('Опубликовать')