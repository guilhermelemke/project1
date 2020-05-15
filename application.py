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

@app.route("/search", methods=['POST'])
def search():
    name = request.form.get('username')
    password = request.form.get('password')
    if db.execute("SELECT * FROM users WHERE users.user = :name AND users.password = :password", {"name": name, "password": password}).rowcount == 1:
        return render_template("search.html", username=name)
    return render_template('error.html')

@app.route("/registuser", methods=['GET'])
def registuser():
    return render_template('register.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    name = request.form.get('username')
    password = request.form.get('password')
    if db.execute("SELECT * FROM users WHERE users.user = :name", {"name": name}).rowcount == 1:
        return render_template('error.html')
    db.execute("INSERT INTO users (user, password) VALUES (:name, :password)", {"name": name, "password": password})
    db.commit()
    return render_template("search.html", username=name)