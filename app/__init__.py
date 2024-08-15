import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flasgger import Swagger
from flask_session import Session

from config import Config
from app.utils.auth import setup_oauth

import json


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()
session = Session()


swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Request Processing API",
        "description": "API for secure request processing system",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "OAuth2": {
            "type": "oauth2",
            "flow": "implicit",
            "authorizationUrl": "https://accounts.google.com/o/oauth2/auth",
            "scopes": {
                "email": "Access to user email"
            },
            "x-google-issuer": "https://accounts.google.com",
            "x-google-jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
            "x-google-audiences": Config.OAUTH_CLIENT_ID
        }
    },
    "security": [
        {"OAuth2": ["email"]}
    ]
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
    "oauth_config": {
        "clientId": Config.OAUTH_CLIENT_ID,
        "scopes": ["email"],
        "appName": "Your App Name",
        "usePkceWithAuthorizationCodeGrant": False
    }
}
swagger = Swagger(template=swagger_template, config=swagger_config)


def setup_logging(app):
    class RequestFormatter(logging.Formatter):
        def format(self, record):
            record.url = request.url if request else "N/A"
            record.remote_addr = request.remote_addr if request else "N/A"
            return json.dumps({
                'timestamp': self.formatTime(record, self.datefmt),
                'level': record.levelname,
                'message': record.getMessage(),
                'url': record.url,
                'remote_addr': record.remote_addr,
                'module': record.module,
                'funcName': record.funcName,
                'lineno': record.lineno
            })

    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Create handlers for different log levels
    handlers = {
        'error': TimedRotatingFileHandler('logs/error.log', when='midnight', backupCount=30),
        'warning': TimedRotatingFileHandler('logs/warning.log', when='midnight', backupCount=30),
        'info': TimedRotatingFileHandler('logs/info.log', when='midnight', backupCount=30),
    }

    for handler in handlers.values():
        handler.setFormatter(RequestFormatter())

    handlers['error'].setLevel(logging.ERROR)
    handlers['warning'].setLevel(logging.WARNING)
    handlers['info'].setLevel(logging.INFO)

    # Remove existing handlers
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)

    # Add new handlers
    for handler in handlers.values():
        app.logger.addHandler(handler)

    app.logger.setLevel(logging.INFO)



def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    session.init_app(app)
    CORS(app)
    swagger.init_app(app)

    # Setup OAuth
    setup_oauth(app)

    # Set up logging
    setup_logging(app)

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
    
    from app.routes import auth
    app.register_blueprint(auth.bp)
    
    

    return app
