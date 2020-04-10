from flask import jsonify
from flask_restful import abort, Resource

from data import db_session
from flask_restful import reqparse
from data.books import Books


def abort_if_user_not_found(books_id):
    session = db_session.create_session()
    books = session.query(Books).get(books_id)
    if not books:
        abort(404, message=f"Books {books_id} not found")


class BooksResource(Resource):
    def parse(self):
        parser = reqparse.RequestParser()
        parser.add_argument('author_id', required=False)
        parser.add_argument('title', required=False)
        parser.add_argument('date', required=False)
        parser.add_argument('price', required=False)
        return parser

    def get(self, books_id):
        abort_if_user_not_found(books_id)
        session = db_session.create_session()
        books = session.query(Books).get(books_id)
        return jsonify({'books': books.to_dict(
            only=('author_id', 'title', 'date', 'price'))})

    def delete(self, books_id):
        abort_if_user_not_found(books_id)
        session = db_session.create_session()
        book = session.query(Books).get(books_id)
        session.delete(book)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, books_id):
        abort_if_user_not_found(books_id)
        args = self.parse().parse_args()
        session = db_session.create_session()
        book = session.query(Books).get(books_id)
        if args['author_id'] is not None:
            book.surname = args['author_id']
        if args['title'] is not None:
            book.name = args['title']
        if args['date'] is not None:
            book.age = args['date']
        if args['price'] is not None:
            book.position = args['price']
        session.commit()
        return jsonify({'success': 'OK'})


class BooksListResource(Resource):
    def parse(self):
        parser = reqparse.RequestParser()
        parser.add_argument('author_id', required=True)
        parser.add_argument('title', required=True)
        parser.add_argument('date', required=True)
        parser.add_argument('price', required=True)
        return parser

    def get(self):
        session = db_session.create_session()
        book = session.query(Books).all()
        return jsonify({'books': [item.to_dict(
            only=('author_id', 'title', 'date', 'price')) for item in book]})

    def post(self):
        args = self.parse().parse_args()
        session = db_session.create_session()
        book = Books(
            author_id=args['author_id'],
            title=args['title'],
            date=args['date'],
            price=args['price'])
        book.set_password(book.hashed_password)
        session.add(book)
        session.commit()
        return jsonify({'success': 'OK'})
