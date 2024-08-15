from flask import Blueprint, jsonify, session

bp = Blueprint('auth', __name__)

@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"msg": "Logged out successfully"}), 200