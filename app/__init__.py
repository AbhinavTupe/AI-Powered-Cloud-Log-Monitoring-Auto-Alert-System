from flask import Flask

from app.config import Config
from app.database import close_db, init_db
from app.routes import register_routes
from app.utils.logging_config import configure_logging


def create_app(test_config=None):
    """Application factory used by Flask, tests, and Gunicorn."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    configure_logging(app.config["LOG_LEVEL"])
    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    register_routes(app)
    register_error_handlers(app)
    return app


def register_error_handlers(app):
    @app.errorhandler(ValueError)
    def handle_bad_request(error):
        return {"error": "bad_request", "message": str(error)}, 400
