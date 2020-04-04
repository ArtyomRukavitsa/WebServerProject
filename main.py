from flask import Flask, render_template, redirect, jsonify, make_response, request, abort
from data import db_session
from flask_login import current_user
from data.users import User

app = Flask(__name__)


def main():
    db_session.global_init("db/book_shop.sqlite")
    app.run()


@app.route('/')
@app.route('/main')
def index():
    return render_template("main.html", title='Гланвая')


if __name__ == '__main__':
    main()