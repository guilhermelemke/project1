import os, requests

from flask import Flask, session, render_template, request, redirect, url_for, json, jsonify, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/login", methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if db.execute("SELECT * FROM users WHERE users.username = :name AND users.password = :password",
        {"name": username, "password": password}).rowcount == 1:
        session['username'] = username
        return render_template("search.html", username=username)
    return render_template('error.html')

@app.route("/registuser", methods=['GET', 'POST'])
def registuser():
    return render_template('register.html')

@app.route("/register", methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    try:
        db.execute("INSERT INTO users (username, password) VALUES (:user, :password)",
            {"user": username, "password": password})
        db.commit()
        return render_template("search.html", username=username)
    except:
        return render_template('error.html')

@app.route("/search", methods=['POST'])
def search():
    option = request.form.get('options')
    search = request.form.get('search')

    books = db.execute(f"SELECT * FROM books WHERE LOWER({option}) LIKE LOWER(:search)",
        {"search": '%'+search+'%'}).fetchall()
    return render_template("results.html", books=books)

@app.route("/logout", methods=['GET'])
def logout():
    return render_template('index.html')

@app.route("/details", methods=['GET'])
def details():
    isbn = request.args.get('isbn')
    book_info = db.execute(f"SELECT * FROM books WHERE isbn = :selected_book",
        {"selected_book": isbn}).fetchall()

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "OoKksVO9s5wfeWe9XAtrw", "isbns": isbn})
    response = res.json()
    average_rating = response['books'][0]['average_rating']
    ratings_count = response['books'][0]['ratings_count']

    return render_template('details.html', book=book_info, average_rating=average_rating, ratings_count=ratings_count)

@app.route("/review", methods=['POST'])
def review():
    rating = request.form.get('ratings')
    description = request.form.get('description')
    isbn = request.args.get('isbn')

    if db.execute("SELECT * FROM ratings WHERE username = :username AND isbn = :isbn",
        {"username": session['username'], "isbn": isbn}).rowcount == 0:
            db.execute("INSERT INTO ratings (review_rating, description, isbn, username) VALUES (:review_rating, :description, :isbn, :username)",
                {"review_rating": rating, "description": description, "isbn": isbn, "username": session['username']})
            db.commit()
            return render_template("reviewed.html")
    return render_template("error.html")

@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.route("/api/<isbn>", methods=['GET'])
def api(isbn):
    book_info = db.execute(f"SELECT * FROM books WHERE isbn = :selected_book",
        {"selected_book": isbn}).fetchall()
    if book_info: 
            res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "OoKksVO9s5wfeWe9XAtrw", "isbns": isbn})
            response = res.json()
            average_rating = response['books'][0]['average_rating']
            ratings_count = response['books'][0]['ratings_count']

            book_details = dict(title=book_info[0][0],
                                author=book_info[0][2],
                                year=book_info[0][3],
                                isbn=isbn,
                                average_rating=average_rating,
                                ratings_count=ratings_count)
            json = jsonify(book_details)

            return json
    abort(404, description="Resource not found")
    return jsonify()  
