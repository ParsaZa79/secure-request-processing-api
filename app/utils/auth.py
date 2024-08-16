from flask import jsonify, current_app, request
from functools import wraps
from flask_dance.contrib.google import make_google_blueprint
import requests

# def setup_oauth(app):
#     oauth_bp = make_google_blueprint(
#         client_id=app.config['OAUTH_CLIENT_ID'],
#         client_secret=app.config['OAUTH_CLIENT_SECRET'],
#         scope=["profile", "email"],
#         redirect_to="main.callback"  # Ensure you have a callback route defined
#     )
#     app.register_blueprint(oauth_bp, url_prefix="/login")
#     return oauth_bp

# def oauth_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         auth_header = request.headers.get('Authorization')
#         current_app.logger.info(f"Authorization header: {auth_header}")
#         if not auth_header:
#             current_app.logger.error("No Authorization header present")
#             return jsonify({"msg": "Missing Authorization header"}), 401

#         parts = auth_header.split()
#         if parts[0].lower() != 'bearer':
#             current_app.logger.error("Authorization header must start with Bearer")
#             return jsonify({"msg": "Invalid Authorization header"}), 401
#         elif len(parts) == 1:
#             current_app.logger.error("Token not found in Authorization header")
#             return jsonify({"msg": "Token not found"}), 401
#         elif len(parts) > 2:
#             current_app.logger.error("Authorization header must be Bearer token")
#             return jsonify({"msg": "Invalid Authorization header"}), 401

#         token = parts[1]
#         try:
#             headers = {'Authorization': f'Bearer {token}'}
#             resp = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers)
#             if resp.status_code == 200:
#                 # Token is valid
#                 return f(*args, **kwargs)
#             else:
#                 current_app.logger.error(f"OAuth2 token validation failed: {resp.text}")
#                 return jsonify({"msg": "Invalid token"}), 401
#         except Exception as e:
#             current_app.logger.error(f"OAuth2 token validation failed: {str(e)}")
#             return jsonify({"msg": f"{str(e)}"}), 401

#     return decorated

def oauth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        current_app.logger.info(f"Authorization header: {auth_header}")
        
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
            decoded_token = decode_session_token(session_token)
            
            # Check if the token has expired
            if decoded_token['exp'] < datetime.utcnow().timestamp():
                current_app.logger.error("Session token has expired")
                return jsonify({"msg": "Session expired"}), 401
            
            # Get the user from the database using the session token
            user = get_user_by_session_token(session_token)
            
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