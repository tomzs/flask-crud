from flask import Flask, render_template, flash, redirect
from flask import url_for, session, logging, request

from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from data_functions import register_user, check_user, get_password_hash
from data_functions import create_post, get_user_posts, get_all_posts, get_post, edit_post, delete_post
from functools import wraps
import json


app = Flask(__name__)
SECRET_KEY = ""
with open("db_conn.json") as dbc:
    SETTINGS = json.load(dbc)

# Index route
@app.route('/')
def index():
    return render_template("home.html")

# About route
@app.route('/about')
def about():
    return render_template("about.html")

# Posts route, shows every post in db.
@app.route('/posts')
def posts_page():
    results = get_all_posts()

    if results is not None:
        return render_template('posts.html', posts=results)
    else:
        msg = "No articles found"
        return render_template('posts.html', msg=msg)

# Post route, shows specific post.
@app.route('/post/<string:id>/')
def post_page(id):
    target_post = get_post(id)
    return render_template("post.html", post = target_post)

# Register form using WTForms
class RegisterForm(Form):
    name = StringField("Name", [validators.Length(min=1, max=32)])
    username = StringField('Username', [validators.Length(min=3, max=32)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField("Password", [
        validators.DataRequired(),
        validators.EqualTo("confirm", message="Passwords dont match")
    ])
    confirm = PasswordField("Confirm Password")

# Register route
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.hash(str(form.password.data))
        if check_user(username):
            register_user(name, email, username, password)
            flash("Succesful registration", 'success')
            return redirect(url_for('login'))
        else:
            flash("Failed to register", 'danger')
    return render_template('register.html', form=form)

# Login Route
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password_in = request.form["password"]
        # check_user function needs some work
        if check_user(username) is False:
            if sha256_crypt.verify(password_in, get_password_hash(username)):
                # Logged in
                session['logged_in'] = True
                session['username'] = username
                print(f"Session: {session}")
                print(f"Session type: {type(session)}")

                flash("Logged in successfully", 'success')
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid login"
                return render_template('login.html', error=error)
        else:
            error = "User not found"
            return render_template('login.html', error=error)
    return render_template('login.html')

# Checks if user is logged in by checking Flask session.
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash("You've logged out!", 'success')
    return redirect(url_for('login'))

# Dashboard route, lets user create, edit and delete posts.
@app.route('/dashboard')
@is_logged_in
def dashboard():

    results = get_user_posts(session['username'])

    if results is not None:
        return render_template('dashboard.html', posts=results)
    else:
        msg = "No articles found"
        return render_template('dashboard.html', msg=msg)

# WTForm for Post.
class PostForm(Form):
    title = StringField("Title", [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=25)])

# Add post route
@app.route('/add_post', methods=["GET", "POST"])
@is_logged_in
def add_post():
    form = PostForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        body = form.body.data

        create_post(session['username'], title, body)

        flash("Post was created!", "success")

        return redirect(url_for('dashboard'))

    return render_template('add_post.html', form=form)

# Edit post route
@app.route('/edit_post/<string:id>', methods=["GET", "POST"])
@is_logged_in
def update_post(id):

    post = get_post(id)

    form = PostForm(request.form)

    form.title.data = post['title']
    form.body.data = post['body']

    if request.method == "POST" and form.validate():
        title = request.form['title']
        body = request.form['body']
        edit_post(id, title, body)
        flash("Post was updated succesfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('edit_post.html', form=form)

# Delete post route
@app.route('/delete_post/<string:id>', methods=["POST"])
@is_logged_in
def remove_post(id):
    delete_post(id)
    flash("Post deleted!", 'info')
    return redirect(url_for('dashboard'))


if __name__ == "__main__":
    app.secret_key = SETTINGS["SECRET_KEY"]
    app.run(debug=True)
