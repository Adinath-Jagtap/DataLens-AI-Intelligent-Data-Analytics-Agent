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

    # ── OAuth (Flask-Dance) ───────────────────────────────────────────────
    from flask_dance.contrib.google import make_google_blueprint
    from flask_dance.contrib.github import make_github_blueprint

    google_bp = make_google_blueprint(
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        scope=["openid",
               "https://www.googleapis.com/auth/userinfo.email",
               "https://www.googleapis.com/auth/userinfo.profile"],
        redirect_to="auth.oauth_google_callback",
    )
    github_bp = make_github_blueprint(
        client_id=app.config["GITHUB_CLIENT_ID"],
        client_secret=app.config["GITHUB_CLIENT_SECRET"],
        scope="user:email",
        redirect_to="auth.oauth_github_callback",
    )

    app.register_blueprint(google_bp, url_prefix="/oauth")
    app.register_blueprint(github_bp, url_prefix="/oauth")

    if app.debug:
        import os as _os
        _os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # ── MongoDB indexes ───────────────────────────────────────────────────
    try:
        db.analyses.create_index([("share_token", 1)], sparse=True)
        db.users.create_index(
            [("oauth_providers.provider", 1), ("oauth_providers.provider_id", 1)]
        )
        db.users.create_index([("email", 1)], unique=True)
    except Exception:
        pass

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
