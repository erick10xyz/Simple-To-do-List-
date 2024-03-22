from flask_bootstrap import Bootstrap5
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
# Import your forms from the forms.py
from forms import CreateTask, RegisterForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task.db'
db = SQLAlchemy()
db.init_app(app)


# Create relationship which stores in database of user own login and own to do list
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    task = relationship("Todo", back_populates="author")

#  Create To do list
class Todo(db.Model):
    __tablename__ = "to-do"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = relationship("User", back_populates="task")
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))


with app.app_context():
    db.create_all()

# Start Page
@app.route("/")
def opening_page():
    return render_template("startpage.html")

#  User Login
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()

        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again.")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html", form=form, current_user=current_user)


# Sign up or register to get access/store own personal to do list,
# Store user information for logins
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method="pbkdf2:sha256",
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            password=hash_and_salted_password
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('login'))
    return render_template("register.html", form=form, current_user=current_user)

# Homepage
@app.route("/home")
def home():
    return render_template("index.html")

# Title List you created
@app.route("/task_list")
def tasklist():
    result = db.session.execute(db.select(Todo))
    tasks = result.scalars().all()
    return render_template("tasklist.html", tasks=tasks, current_user=current_user)

#  Show your created to do list
@app.route("/read", methods=["GET", "POST"])
def show():
    task_id = request.args.get("id")
    requested_task = db.get_or_404(Todo, task_id)
    edit_form = CreateTask(
        title=requested_task.title,
        author=requested_task.author,
        body=requested_task.body)
    if edit_form.validate_on_submit():
        requested_task.title = edit_form.title.data
        requested_task.author = current_user
        requested_task.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("tasklist", task_id=requested_task.id))
    return render_template("read.html", task=requested_task, form=edit_form, current_user=current_user)


# Logout User
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('opening_page'))


# Add Another To do List
@app.route("/new-task", methods=["GET", "POST"])
def add_task():
    form = CreateTask()
    if form.validate_on_submit():
        new_task = Todo(
            title=form.title.data,
            body=form.body.data,
            author=current_user,
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("create.html", form=form, current_user=current_user)


#  Delete done task or being cancelled
@app.route("/delete")
def delete_task():
    task_id = request.args.get("id")
    task = db.get_or_404(Todo, task_id)

    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
