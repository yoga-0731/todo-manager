from flask import Flask, render_template, flash, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, logout_user, LoginManager, current_user, login_manager
from forms import RegisterForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap
from flask_cors import CORS
from traceback import format_exc

app = Flask(__name__)
CORS(app, resources={r"/completed": {"origins": "http://127.0.0.1:5000"}})

app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo-manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(30))
    name = db.Column(db.String(40))


class TodoList(db.Model):
    __tablename__ = "todo_list"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    list = db.Column(db.String(250))
    complete = db.Column(db.Boolean, default=False)


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    if current_user.is_authenticated:
        return render_template('index.html', name=current_user.name, todos=get_all_todos(), completed_items=get_completed_items())
    else:
        return redirect(url_for('login'))


@app.route('/', methods=["GET", "POST"])
def add_todo():
    new_todo = TodoList(list=request.form.get('todo-item'), user_id=current_user.id)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for('home'))


def get_all_todos():
    return db.session.query(TodoList).filter_by(user_id=current_user.id, complete=False)


def get_completed_items():
    return db.session.query(TodoList).filter_by(user_id=current_user.id, complete=True)


@app.route('/completed', methods=["GET", "POST"])
def completed():
    try:
        item_id = request.json.get('item_id')
        # print(item_id)
        item = db.session.query(TodoList).filter_by(id=item_id).first()

        if item:
            item.complete = True
            db.session.commit()
            return redirect(url_for('home'))
        else:
            return "Item not found", 404
    except Exception as e:
        print("Error:", e)
        print(format_exc())
        return "An error occurred", 500


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        if db.session.query(User).filter_by(email=email).first():
            flash("You've already signed up with email ID. Please login!")
            return redirect(url_for('login'))
        else:
            hash_and_salted_password = generate_password_hash(
                form.password.data,
                method='pbkdf2:sha256',
                salt_length=8
            )
            new_user = User(email=email, name=form.name.data, password=hash_and_salted_password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("home"))

    return render_template("register.html", form=form)


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).filter_by(id=int(user_id)).first()


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        if db.session.query(User).filter_by(email=email).first():
            password = form.password.data
            user = db.session.query(User).filter_by(email=email).first()
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash("The password is incorrect!")
        else:
            flash("This email ID doesn't exist. Please signup!")
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)


