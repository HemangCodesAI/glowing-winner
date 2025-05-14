from flask import Flask
from .extensions import mail , db
from .routes.auth_routes import auth_bp
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mail.init_app(app)
    db.init_app(app)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    return app
