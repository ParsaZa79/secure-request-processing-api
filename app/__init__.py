import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flasgger import Swagger

from config import Config
from app.utils.auth import setup_oauth

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Request Processing API",
        "description": "API for secure request processing system",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header"
        },
        "OAuth2": {
            "type": "oauth2",
            "flow": "implicit",
            "authorizationUrl": "https://accounts.google.com/o/oauth2/auth",
            "scopes": {
                "email": "Access to user email",
                "profile": "Access to user profile"
            },
            "x-google-issuer": "https://accounts.google.com",
            "x-google-jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
            "x-google-audiences": Config.OAUTH_CLIENT_ID  # Add this line
        }
    },
    "security": [
        {"Bearer": []},
        {"OAuth2": ["email", "profile"]}
    ]
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
    "oauth_config": {  # Add this section
        "clientId": Config.OAUTH_CLIENT_ID,
        "clientSecret": Config.OAUTH_CLIENT_SECRET,
        "appName": "Your App Name"
    }
}

swagger = Swagger(template=swagger_template, config=swagger_config)
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    CORS(app)
    swagger.init_app(app)

    # Setup OAuth
    oauth_provider = setup_oauth(app)

    # Set up logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Request Processing API startup')

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error('Not found: %s', (error))
        return jsonify(error="Not found"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error('Server Error: %s', (error))
        return jsonify(error="Internal server error"), 500

    from app.routes import main
    app.register_blueprint(main.bp)

    from app.routes import logs
    app.register_blueprint(logs.bp)

    return app
