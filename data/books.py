import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Books(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'books'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    author_id = sqlalchemy.Column(sqlalchemy.Integer,
                                    sqlalchemy.ForeignKey("author.id"))  # связывем книгу с автором
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)  # название книги
    date = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)    # дата издания
    cover = sqlalchemy.Column(sqlalchemy.String, nullable=False)  # обложка книги
    author = orm.relation("Author")
