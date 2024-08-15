from flask import Blueprint, request, jsonify, current_app, session
from app.models.request import Request
from app import db
from app.services.queue_service import queue_service
from functools import wraps
from flasgger import swag_from
import requests

bp = Blueprint('main', __name__)

def session_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"msg": "Invalid or missing session"}), 401
        return f(*args, **kwargs)
    return decorated

@bp.route('/exchange-token', methods=['POST'])
def exchange_token():
    auth_code = request.json.get('code')
    if not auth_code:
        return jsonify({"msg": "Missing authorization code"}), 400

    # Exchange the auth code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': auth_code,
        'client_id': current_app.config['OAUTH_CLIENT_ID'],
        'client_secret': current_app.config['OAUTH_CLIENT_SECRET'],
        'redirect_uri': 'YOUR_REDIRECT_URI',  # Must match the one used in your React app
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

    # Store user info and tokens in session
    session['user_id'] = user_info['sub']
    session['access_token'] = tokens['access_token']
    session['refresh_token'] = tokens.get('refresh_token')

    return jsonify({"msg": "Session created successfully"}), 200

@bp.route('/submit-request', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': 'User query to be processed'
                    }
                },
                'required': ['query']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Request submitted successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'request_id': {'type': 'integer'}
                }
            }
        }
    }
})
def submit_request():
    data = request.json
    new_request = Request(user_query=data['query'])
    db.session.add(new_request)
    db.session.commit()
    queue_service.enqueue(new_request)
    current_app.logger.info(f"New request submitted with ID: {new_request.id}")
    return jsonify({'request_id': new_request.id}), 200

@bp.route('/fetch-requests', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'Latest queued request',
            'schema': {
                'type': 'object',
                'properties': {
                    'request_id': {'type': 'integer'},
                    'query': {'type': 'string'}
                }
            }
        }
    }
})
def fetch_requests():
    request = queue_service.dequeue()
    if request:
        current_app.logger.info(f"Request fetched with ID: {request.id}")
        return jsonify({'request_id': request.id, 'query': request.query}), 200
    current_app.logger.info("No requests in queue")
    return jsonify({'message': 'No requests in queue'}), 404

@bp.route('/submit-result', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'request_id': {
                        'type': 'integer',
                        'description': 'ID of the processed request'
                    },
                    'result': {
                        'type': 'string',
                        'description': 'Processed result'
                    }
                },
                'required': ['request_id', 'result']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Result submitted successfully'
        },
        404: {
            'description': 'Request not found'
        }
    }
})
def submit_result():
    data = request.json
    req = Request.query.get(data['request_id'])
    if req:
        req.result = data['result']
        req.status = 'completed'
        db.session.commit()
        current_app.logger.info(f"Result submitted for request ID: {req.id}")
        return jsonify({'message': 'Result submitted successfully'}), 200
    current_app.logger.warning(f"Attempt to submit result for non-existent request ID: {data['request_id']}")
    return jsonify({'message': 'Request not found'}), 404

@bp.route('/get-result/<int:request_id>', methods=['GET'])
@swag_from({
    'parameters': [
        {
            'name': 'request_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID of the request'
        }
    ],
    'responses': {
        200: {
            'description': 'Request result',
            'schema': {
                'type': 'object',
                'properties': {
                    'result': {'type': 'string'},
                    'status': {'type': 'string'}
                }
            }
        }
    }
})
def get_result(request_id):
    req = Request.query.filter_by(id=request_id).first()
    if req:
        current_app.logger.info(f"Result retrieved for request ID: {request_id}")
        return jsonify({'result': req.result, 'status': req.status}), 200
    current_app.logger.warning(f"Attempt to get result for non-existent request ID: {request_id}")
    return jsonify({'message': 'Request not found'}), 404