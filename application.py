import os

from flask import Flask, session, render_template, request
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

@app.route("/search", methods=['GET'])
def search():
    option = request.form.get('options')
    search = request.form.get('search')

    book = db.execute(f"SELECT * FROM books WHERE {option} = :search", {"search": search}).fetchall()
    return render_template("results.html", book=book)
