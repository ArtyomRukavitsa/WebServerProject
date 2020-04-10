from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired


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
