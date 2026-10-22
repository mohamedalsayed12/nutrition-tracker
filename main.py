from flask import Flask
from flask_cors import CORS

from config import ROOT, load_config
from database import init_database
from errors import register_error_handlers
from oauth2 import jwt
from routers import register_routes
from routers.pages import register_pages
from routers.pwa import register_pwa
from sessions import login_manager
from utils import bcrypt


def create_app(test_config=None):
    app = Flask(__name__, static_folder=None, instance_path=str(ROOT / "instance"))
    app.config.update(load_config(test_config))
    app.config.update(test_config or {})
    if not app.config["SECRET_KEY"] or not app.config["JWT_SECRET_KEY"]:
        raise RuntimeError("Set SECRET_KEY and JWT_SECRET_KEY in the environment.")
    init_database(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    if app.config["FRONTEND_ORIGINS"]:
        CORS(app, resources={r"/api/*": {"origins": app.config["FRONTEND_ORIGINS"]}})
    login_manager.init_app(app)
    register_error_handlers(app)
    register_routes(app)
    register_pages(app)
    register_pwa(app)
    return app
