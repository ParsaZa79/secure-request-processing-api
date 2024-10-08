from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request, current_app, session
import jwt
import requests
from urllib.parse import urlencode
from app import db

from app.models.user import User

bp = Blueprint('auth', __name__)


@bp.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"msg": "Logged out successfully"}), 200

@bp.route('/api/auth/google', methods=['POST'])
def google_auth():
    try:
        auth_code = request.json.get('code')
        
        # current_app.logger.info(f"Auth code: {auth_code}")
        
        if not auth_code:
            return jsonify({"msg": "Missing authorization code"}), 400

        # Exchange the auth code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'code': auth_code,
            'client_id': current_app.config['GOOGLE_OAUTH_CLIENT_ID'],
            'client_secret': current_app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
            'redirect_uri': current_app.config['GOOGLE_OAUTH_REDIRECT_URI'],
            'grant_type': 'authorization_code'
        }
        response = requests.post(token_url, data=data)

        if response.status_code != 200:
            return jsonify({"msg": "Failed to exchange token"}), 400

        tokens = response.json()

        # Use the access token to get user info
        user_info_response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', 
                                        headers={'Authorization': f"Bearer {tokens['access_token']}"})

        if user_info_response.status_code != 200:
            return jsonify({"msg": "Failed to get user info"}), 400

        user_info = user_info_response.json()

        
        # Create a session token
        user = User.query.filter_by(google_id=user_info['sub']).first()
        if not user:
            user = User(
                google_id=user_info['sub'],
                username=None,
                name=user_info.get('name'),
                email=user_info.get('email'),
                picture=user_info.get('picture'),
                session_expiration=datetime.now(timezone.utc) + timedelta(days=1)
            )
            db.session.add(user)
            db.session.commit()
        
        # Create a session token
        session_token = jwt.encode(
            {
                'id': str(user.id),
                'email': user_info['email'],
                'name': user_info['name'],
                'picture': user_info.get('picture'),
                'username': None,
                'exp': int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp())
            },
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        # Update the user with the session token
        user.session_token = session_token
        db.session.commit()

        return jsonify({
            "session_token": session_token,
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error exchanging code for tokens: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500



@bp.route('/api/auth/github', methods=['POST'])
def github_auth():
    try:
        auth_code = request.json.get('code')
        
        # current_app.logger.info(f"Auth code: {auth_code}")
        

        token_exchange_url = 'https://github.com/login/oauth/access_token'
        token_exchange_headers = {
            "Accept": "application/json",
            "Accept-Encoding": "application/json",
        }
        token_exchange_params = {
            'client_id': current_app.config['GITHUB_OAUTH_CLIENT_ID'],
            'client_secret': current_app.config['GITHUB_OAUTH_CLIENT_SECRET'],
            'code': auth_code,
            'redirect_uri': current_app.config['GITHUB_OAUTH_REDIRECT_URI'],
        }

        response = requests.post(token_exchange_url, headers=token_exchange_headers, params=token_exchange_params)
        
        if response.status_code != 200:
            return jsonify({"msg": "Failed to exchange token"}), 400
        
        access_token = response.json().get('access_token')
        
        if not access_token:
            return jsonify({"msg": "Missing access token"}), 400

        # Use the access token to get user info
        user_info_url = 'https://api.github.com/user'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }
        user_info_response = requests.get(user_info_url, headers=headers)

        if user_info_response.status_code != 200:
            return jsonify({"msg": "Failed to get user info"}), 400

        user_info = user_info_response.json()

        user = User.query.filter_by(github_id=user_info['id']).first()
        if not user:
            user = User(
                github_id=user_info['id'],
                username=user_info['login'],
                name=user_info.get('name'),
                email=user_info.get('email'),
                picture=user_info.get('avatar_url'),
                session_expiration=datetime.now(timezone.utc) + timedelta(days=1)
            )
            db.session.add(user)
            db.session.commit()
        
        # Create a session token
        session_token = jwt.encode(
            {
                'id': str(user.id),
                'username': user_info['login'],
                'name': user_info.get('name'),
                'email': user_info.get('email'),
                'picture': user_info.get('avatar_url'),
                'exp': int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp())
            },
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        # Update the user with the session token
        user.session_token = session_token
        db.session.commit()
        
        return jsonify({
            "session_token": session_token,
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error processing GitHub auth: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500