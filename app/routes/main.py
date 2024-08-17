from flask import Blueprint, request, jsonify, current_app, session
from app.models.request import Request
from app import db
from app.models.user import User
from app.services.queue_service import queue_service
from functools import wraps
from flasgger import swag_from
import requests

from app.utils.auth import oauth_required

bp = Blueprint('main', __name__)

def session_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"msg": "Invalid or missing session"}), 401
        return f(*args, **kwargs)
    return decorated

@bp.route('/submit-request', methods=['POST'])
@oauth_required
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
    user = request.current_user
    new_request = Request(user_query=data['query'], user_id=user.id)
    db.session.add(new_request)
    db.session.commit()
    queue_service.enqueue(new_request)
    current_app.logger.info(f"New request submitted with ID: {new_request.id} for user: {user.id}")
    return jsonify({'request_id': new_request.id}), 200

@bp.route('/fetch-requests', methods=['GET'])
@oauth_required
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

@bp.route('/requests', methods=['GET'])
@oauth_required
@swag_from({
    'responses': {
        200: {
            'description': 'List of user\'s requests',
            'schema': {
                'type': 'object',
                'properties': {
                    'requests': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'user_query': {'type': 'string'},
                                'status': {'type': 'string'},
                                'result': {'type': 'string'},
                                'created_at': {'type': 'string', 'format': 'date-time'},
                                'updated_at': {'type': 'string', 'format': 'date-time'}
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_user_requests():
    user = request.current_user
    user_requests = Request.query.filter_by(user_id=user.id).all()
    
    requests_data = [{
        'id': req.id,
        'user_query': req.user_query,
        'status': req.status,
        'result': req.result,
        'created_at': req.created_at.isoformat(),
        'updated_at': req.updated_at.isoformat()
    } for req in user_requests]
    
    current_app.logger.info(f"User {user.id} retrieved their requests")
    return jsonify({'requests': requests_data}), 200

@bp.route('/submit-result', methods=['POST'])
@oauth_required
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
@oauth_required
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
        return jsonify({'result': req.result, 'status': req.status, 'request_id': request_id}), 200
    current_app.logger.warning(f"Attempt to get result for non-existent request ID: {request_id}")
    return jsonify({'message': 'Request not found'}), 404