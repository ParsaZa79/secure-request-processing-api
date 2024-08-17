from datetime import datetime
from flask import jsonify, current_app, request
from functools import wraps
from flask_dance.contrib.google import make_google_blueprint
import requests
import jwt
from uuid import UUID
from app.models.user import User

import jwt
from typing import TypedDict, Optional

class DecodedToken(TypedDict):
    username: str
    email: str
    name: str
    picture: str
    exp: int

def decode_token(stored_token: str) -> Optional[DecodedToken]:
    try:
        decoded = jwt.decode(stored_token, options={"verify_signature": False})
        return DecodedToken(
            id=decoded.get('id', ''),
            username=decoded.get('username', ''),
            email=decoded.get('email', ''),
            name=decoded.get('name', ''),
            picture=decoded.get('picture', ''),
            exp=decoded.get('exp', 0)
        )
    except jwt.DecodeError:
        print("Failed to decode token")
        return None

def oauth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            current_app.logger.error("No Authorization header present")
            return jsonify({"msg": "Missing Authorization header"}), 401

        parts = auth_header.split()
        if parts[0].lower() != 'bearer':
            current_app.logger.error("Authorization header must start with Bearer")
            return jsonify({"msg": "Invalid Authorization header"}), 401
        elif len(parts) == 1:
            current_app.logger.error("Token not found in Authorization header")
            return jsonify({"msg": "Token not found"}), 401
        elif len(parts) > 2:
            current_app.logger.error("Authorization header must be Bearer token")
            return jsonify({"msg": "Invalid Authorization header"}), 401

        session_token = parts[1]
        
        try:
            # Decode the session token
            decoded_token = decode_token(session_token)
            
            # Check if the token has expired
            if decoded_token['exp'] < datetime.now().timestamp():
                current_app.logger.error("Session token has expired")
                return jsonify({"msg": "Session expired"}), 401
            
            # Get the user from the database using the session token
            
            user = User.query.filter_by(id=UUID(decoded_token['id'])).first()
            
            if not user:
                current_app.logger.error("No user found for the given session token")
                return jsonify({"msg": "Invalid session"}), 401
            
            # Attach the user to the request for use in the route handler
            request.current_user = user
            
            return f(*args, **kwargs)
        
        except Exception as e:
            current_app.logger.error(f"Session token validation failed: {str(e)}")
            return jsonify({"msg": "Invalid session"}), 401

    return decorated