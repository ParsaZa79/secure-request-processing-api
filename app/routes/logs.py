import os
import json
from flask import Blueprint, jsonify, current_app, send_file, request
from app.utils.auth import oauth_required
from flasgger import swag_from

bp = Blueprint('logs', __name__)

@bp.route('/logs', methods=['GET'])
@oauth_required
@swag_from({
    'responses': {
        200: {
            'description': 'Application logs',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'logs': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'timestamp': {'type': 'string'},
                                        'level': {'type': 'string'},
                                        'message': {'type': 'string'},
                                        'url': {'type': 'string'},
                                        'remote_addr': {'type': 'string'},
                                        'module': {'type': 'string'},
                                        'funcName': {'type': 'string'},
                                        'lineno': {'type': 'integer'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Bad request',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'error': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
})
def get_logs():
    log_type = request.args.get('type', 'info')
    lines = request.args.get('lines', 100, type=int)

    if log_type not in ['error', 'warning', 'info']:
        return jsonify({'error': 'Invalid log type'}), 400

    log_file_path = os.path.join(current_app.root_path, '..', 'logs', f'{log_type}.log')
    
    try:
        with open(log_file_path, 'r') as log_file:
            logs = log_file.readlines()[-lines:]
        
        parsed_logs = [json.loads(log) for log in logs]
        
        current_app.logger.info(f"Retrieved {len(parsed_logs)} {log_type} log entries")
        return jsonify({'logs': parsed_logs}), 200
    except FileNotFoundError:
        current_app.logger.error(f"Log file not found at {log_file_path}")
        return jsonify({'error': 'Log file not found'}), 404
    except json.JSONDecodeError:
        current_app.logger.error(f"Error parsing log file: {log_file_path}")
        return jsonify({'error': 'Error parsing log file'}), 500
    except Exception as e:
        current_app.logger.error(f"Error reading log file: {str(e)}")
        return jsonify({'error': 'Error reading log file'}), 500

@bp.route('/logs/download', methods=['GET'])
@oauth_required
@swag_from({
    'parameters': [
        {
            'name': 'type',
            'in': 'query',
            'type': 'string',
            'enum': ['error', 'warning', 'info'],
            'default': 'info',
            'required': False
        }
    ],
    'responses': {
        200: {
            'description': 'Download application logs',
            'content': {
                'application/octet-stream': {}
            }
        },
        400: {
            'description': 'Bad request',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'error': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
})
def download_logs():
    log_type = request.args.get('type', 'info')

    if log_type not in ['error', 'warning', 'info']:
        return jsonify({'error': 'Invalid log type'}), 400

    log_file_path = os.path.join(current_app.root_path, '..', 'logs', f'{log_type}.log')
    
    try:
        current_app.logger.info(f"Downloading {log_type} log file")
        return send_file(log_file_path, as_attachment=True, download_name=f'{log_type}.log')
    except FileNotFoundError:
        current_app.logger.error(f"Log file not found at {log_file_path}")
        return jsonify({'error': 'Log file not found'}), 404
    except Exception as e:
        current_app.logger.error(f"Error downloading log file: {str(e)}")
        return jsonify({'error': 'Error downloading log file'}), 500