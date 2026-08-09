from flask import Blueprint, jsonify
from middleware.auth import token_required
from database import (
    get_user_notifications,
    get_unread_notification_count,
    mark_notification_read,
    mark_all_notifications_read
)

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/list', methods=['GET'])
@token_required
def list_notifications(current_user_email):
    notifications = get_user_notifications(current_user_email)
    unread_count = get_unread_notification_count(current_user_email)
    return jsonify({"status": "success", "notifications": notifications, "unread_count": unread_count})

@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@token_required
def mark_read(current_user_email, notification_id):
    mark_notification_read(notification_id, current_user_email)
    return jsonify({"status": "success"})

@notifications_bp.route('/read-all', methods=['POST'])
@token_required
def mark_all_read(current_user_email):
    mark_all_notifications_read(current_user_email)
    return jsonify({"status": "success"})