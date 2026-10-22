from flask_login import LoginManager


login_manager = LoginManager()
login_manager.login_view = "auth.login_page"


@login_manager.user_loader
def load_user(uid):
    from database import db
    from models import User

    if isinstance(uid, str) and uid.isdecimal():
        return db.session.get(User, int(uid))
    return None
