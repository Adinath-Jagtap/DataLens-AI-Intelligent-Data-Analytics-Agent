from flask import Flask
from flask_login import LoginManager
from pymongo import MongoClient
from .config import Config

login_manager = LoginManager()
mongo_client  = None
db            = None

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    global mongo_client, db
    mongo_client = MongoClient(app.config["MONGO_URI"])
    db = mongo_client.get_default_database()

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."

    from .auth.routes import auth_bp
    from .main.routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.template_filter("format_number")
    def format_number(value):
        try:
            return f"{int(value):,}"
        except (TypeError, ValueError):
            return value

    @app.context_processor
    def inject_config():
        return {"config": app.config}

    return app
