from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import login_required, current_user, login_user, LoginManager, logout_user, UserMixin
from werkzeug.security import check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config["DEBUG"] = True

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="koreaflagfootbal",
    password="passworddb",
    hostname="koreaflagfootball.mysql.pythonanywhere-services.com",
    databasename="koreaflagfootbal$kfflpage",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.secret_key = "randomsecretkey"
login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.username

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(username=user_id).first()

class Comment(db.Model):

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(4096))
    posted = db.Column(db.DateTime, default=datetime.now)
    commenter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    commenter = db.relationship('User', foreign_keys=commenter_id)

class Winner(db.Model):

    __tablename__ = "winners"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(4096))
    points = db.Column(db.Integer)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("main_page.html", comments=Comment.query.all(), winners=Winner.query.all())
    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    comment = Comment(content=request.form["contents"], commenter=current_user)
    db.session.add(comment)
    db.session.commit()

    return redirect(url_for('index'))

@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login_page.html", error=False)

    user = load_user(request.form["username"])
    if user is None:
        return render_template("login_page.html", error=True)

    if not user.check_password(request.form["password"]):
        return render_template("login_page.html", error=True)

    login_user(user)
    return redirect(url_for('index'))


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/add_points/<int:winner_id>", methods=["POST"])
@login_required
def add_point(winner_id):
    if not current_user.is_authenticated:
        return redirect(url_for("index"))

    winner = Winner.query.get(winner_id)
    if winner is None:
        return redirect(url_for("index"))

    # Increment the points by 1
    winner.points += 1
    db.session.commit()

    return redirect(url_for("index"))

@app.route("/remove_points/<int:winner_id>", methods=["POST"])
@login_required
def remove_point(winner_id):
    if not current_user.is_authenticated:
        return redirect(url_for("index"))

    winner = Winner.query.get(winner_id)
    if winner is None:
        return redirect(url_for("index"))

    # Decrement the points by 1
    winner.points -= 1
    db.session.commit()

    return redirect(url_for("index"))


@app.route("/add_winner", methods=["POST"])
@login_required
def add_winner():
    if not current_user.is_authenticated:
        return redirect(url_for("index"))

    winner_name = request.form.get("winner_name")
    if winner_name:
        new_winner = Winner(name=winner_name, points=0)
        db.session.add(new_winner)
        db.session.commit()

    return redirect(url_for("index"))
