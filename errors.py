from flask import jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from database import db


def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def invalid_input(error):
        return jsonify(error="Invalid request.", details=error.errors(include_url=False, include_context=False, include_input=False)), 400

    @app.errorhandler(ValueError)
    def invalid_value(error):
        db.session.rollback()
        return jsonify(error=str(error)), 400

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    @app.errorhandler(Exception)
    def unexpected_error(error):
        db.session.rollback()
        if app.testing:
            raise error
        app.logger.exception("Request failed")
        return jsonify(error="The request could not be completed."), 500
