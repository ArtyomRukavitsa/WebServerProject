from flask import jsonify
from flask_restful import abort, Resource

from data import db_session
from flask_restful import reqparse
from data.author import Author


def abort_if_user_not_found(author_id):
    session = db_session.create_session()
    author = session.query(Author).get(author_id)
    if not author:
        abort(404, message=f"Author {author_id} not found")


class AuthorsResource(Resource):
    def parse(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=False)
        parser.add_argument('surname', required=False)
        parser.add_argument('years', required=False)
        parser.add_argument('list_of_books', required=False)
        return parser

    def get(self, author_id):
        abort_if_user_not_found(author_id)
        session = db_session.create_session()
        author = session.query(Author).get(author_id)
        return jsonify({'author': author.to_dict(
            only=('name', 'surname', 'years', 'list_of_books'))})

    def delete(self, author_id):
        abort_if_user_not_found(author_id)
        session = db_session.create_session()
        author = session.query(Author).get(author_id)
        session.delete(author)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, author_id):
        abort_if_user_not_found(author_id)
        args = self.parse().parse_args()
        session = db_session.create_session()
        author = session.query(Author).get(author_id)
        if args['surname'] is not None:
            author.surname = args['surname']
        if args['name'] is not None:
            author.name = args['name']
        if args['years'] is not None:
            author.age = args['years']
        if args['list_of_books'] is not None:
            author.position = args['list_of_books']
        session.commit()
        return jsonify({'success': 'OK'})


class AuthorsListResource(Resource):
    def parse(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True)
        parser.add_argument('surname', required=True)
        parser.add_argument('years', required=True)
        parser.add_argument('list_of_books', required=True)
        return parser

    def get(self):
        session = db_session.create_session()
        author = session.query(Author).all()
        return jsonify({'author': [item.to_dict(
            only=('name', 'surname', 'years', 'list_of_books')) for item in author]})

    def post(self):
        args = self.parse().parse_args()
        session = db_session.create_session()
        author = Author(
            surname=args['surname'],
            name=args['name'],
            years=args['years'],
            list_of_books=args['list_of_books'])
        author.set_password(author.hashed_password)
        session.add(author)
        session.commit()
        return jsonify({'success': 'OK'})
