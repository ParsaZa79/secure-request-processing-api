from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request, current_app, session
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import jwt
import os

from app.models.user import User

bp = Blueprint('auth', __name__)

# Set up the OAuth 2.0 flow
flow = Flow.from_client_secrets_file(
            'client_secrets.json',
            scopes=['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
        )
flow.redirect_uri = 'http://localhost:8080/api/auth/google'


@bp.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"msg": "Logged out successfully"}), 200

@bp.route('/api/auth/google', methods=['POST'])
def google_auth():
    try:
        # Get the authorization code from the request
        data = request.get_json()
        code = data.get('code')

        if not code:
            return jsonify({"error": "Authorization code is required"}), 400


        # Exchange the authorization code for tokens
        flow.fetch_token(code=code)

        # Get the credentials
        credentials = flow.credentials

        # Use the credentials to build the OAuth2 service
        oauth2_service = build('oauth2', 'v2', credentials=credentials)

        # Get user info
        user_info = oauth2_service.userinfo().get().execute()

        # Create a session token
        session_token = jwt.encode(
            {
                'email': user_info['email'],
                'name': user_info['name'],
                'picture': user_info.get('picture'),
            },
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            user = User(
                email=user_info['email'],
                name=user_info['name'],
                picture=user_info.get('picture'),
                session_token=session_token,
                session_expiration=datetime.now(timezone.utc) + timedelta(hours=1)
            )
            user.save()

        return jsonify({
            "session_token": session,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error exchanging code for tokens: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@bp.route('/api/auth/google', methods=['GET'])
def google_auth_redirect():
    return jsonify({"msg": "Google auth redirect"}), 200