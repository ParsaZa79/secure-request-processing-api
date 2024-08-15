import os
from flask import Blueprint, jsonify, current_app, send_file
from app.utils.auth import oauth_required
from flasgger import swag_from

bp = Blueprint('logs', __name__)

@bp.route('/logs', methods=['GET'])
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
                                    'type': 'string'
                                }
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_logs():
    log_file_path = os.path.join(current_app.root_path, '..', 'logs', 'app.log')
    try:
        with open(log_file_path, 'r') as log_file:
            logs = log_file.readlines()
        return jsonify({'logs': logs}), 200
    except FileNotFoundError:
        current_app.logger.error(f"Log file not found at {log_file_path}")
        return jsonify({'error': 'Log file not found'}), 404
    except Exception as e:
        current_app.logger.error(f"Error reading log file: {str(e)}")
        return jsonify({'error': 'Error reading log file'}), 500



@bp.route('/logs/download', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'Download application logs',
            'content': {
                'application/octet-stream': {}
            }
        }
    }
})
def download_logs():
    log_file_path = os.path.join(current_app.root_path, '..', 'logs', 'app.log')
    try:
        return send_file(log_file_path, as_attachment=True, download_name='app.log')
    except FileNotFoundError:
        current_app.logger.error(f"Log file not found at {log_file_path}")
        return jsonify({'error': 'Log file not found'}), 404
    except Exception as e:
        current_app.logger.error(f"Error downloading log file: {str(e)}")
        return jsonify({'error': 'Error downloading log file'}), 500