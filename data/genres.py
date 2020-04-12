import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Genre(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'genre'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    genre = sqlalchemy.Column(sqlalchemy.String, nullable=False)  # название жанра

    books = orm.relation("Books", back_populates='genre')  # связывем жанр с книгой
