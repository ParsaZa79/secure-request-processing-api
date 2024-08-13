from flask import Blueprint, request, jsonify, current_app, url_for, session, redirect
from app.models.request import Request
from app import db
from app.services.queue_service import queue_service
from app.utils.auth import auth_required, oauth_required, generate_token
from flasgger import swag_from
from flask_dance.contrib.google import google

bp = Blueprint('main', __name__)

# @bp.route('/login')
# def login():
#     return redirect(url_for('google.login'))

# @bp.route('/login/authorized')
# def authorized():
#     if not google.authorized:
#         return redirect(url_for('google.login'))
#     resp = google.get("/oauth2/v2/userinfo")
#     assert resp.ok, resp.text
#     email = resp.json()["email"]
#     # Here you would typically create or update a user in your database
#     # and then generate a JWT token for them
#     token = generate_token(email)
#     return jsonify({'token': token}), 200

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
    new_request = Request(user_query=data['query'])
    db.session.add(new_request)
    db.session.commit()
    queue_service.enqueue(new_request)
    current_app.logger.info(f"New request submitted with ID: {new_request.id}")
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
        return jsonify({'result': req.result, 'status': req.status}), 200
    current_app.logger.warning(f"Attempt to get result for non-existent request ID: {request_id}")
    return jsonify({'message': 'Request not found'}), 404

# @bp.route('/token', methods=['POST'])
# def get_token():
#     # This route is now deprecated as we're using OAuth2
#     current_app.logger.warning("Deprecated /token route accessed")
#     return jsonify({'message': 'This route is deprecated. Please use OAuth2 for authentication.'}), 410