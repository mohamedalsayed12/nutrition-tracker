
from imports import (flask, Blueprint, login_user, FlaskForm, BooleanField,
                     PasswordField, StringField, SubmitField, DataRequired)
from extensions import bcrypt, login_manager
from db import get_record, user_by_email, add_record, commit_changes
from models import User


auth_bp = Blueprint("auth", __name__)


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


@login_manager.user_loader
def load_user(uid):
    return get_record(User, int(uid))


@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        user = user_by_email(form.email.data.strip().lower())
        if user is None or not bcrypt.check_password_hash(user.password, form.password.data):
            return flask.render_template("login.html", form=form, erorr="Invalid email or password.")
        login_user(user)
        flask.flash("Logged in successful.")
        return flask.redirect(flask.url_for("home_page"))
    if flask.request.method == "POST":
        return flask.render_template("login.html", form=form, erorr="Invalid form. Refresh and try again."), 400
    return flask.render_template("login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def registration_page():
    form = RegistrationForm()
    if flask.request.method == "POST":
        if not form.validate_on_submit():
            return flask.render_template("register.html", form=form, error="Invalid form. Refresh and try again."), 400
        name = form.name.data.strip()
        email = form.email.data.strip().lower()
        password = form.password.data
        if user_by_email(email) is not None:
            return flask.render_template("register.html", form=form, error="Email is already registered."), 409
        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(username=name, email=email, password=password_hash)
        add_record(user)
        commit_changes()
        return flask.redirect(flask.url_for("auth.login_page"))
    return flask.render_template("register.html", form=form)
