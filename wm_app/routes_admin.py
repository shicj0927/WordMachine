from flask import Blueprint, request, jsonify
from .utils import get_db_connection, check_auth, hash_password

bp = Blueprint('admin', __name__)


@bp.route('/api/admin/check', methods=['POST'])
def api_admin_check():
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False}), 400
        
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT type FROM user WHERE id = %s", (uid,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return jsonify({'success': True, 'type': user['type']}), 200
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
    except Exception as e:
        print(f"Admin check error: {e}")
        return jsonify({'success': False}), 500


@bp.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    try:
        uid = request.args.get('uid', type=int)
        pw_hash = request.args.get('pwhash', '').strip()
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
        
        if not uid or not pw_hash:
            return jsonify({'success': False}), 400
        
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT type FROM user WHERE id = %s", (uid,))
        user = cursor.fetchone()
        
        if not user or user['type'] != 'root':
            cursor.close()
            conn.close()
            return jsonify({'success': False}), 403
        
        if include_deleted:
            cursor.execute("SELECT id, username, introduction, rating, type, deleted FROM user ORDER BY id DESC")
        else:
            cursor.execute("SELECT id, username, introduction, rating, type, deleted FROM user WHERE deleted = 0 ORDER BY id DESC")
        
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'users': users}), 200
    except Exception as e:
        print(f"Get users error: {e}")
        return jsonify({'success': False}), 500


@bp.route('/api/admin/user/<int:target_uid>/reset-password', methods=['POST'])
def api_admin_reset_password(target_uid):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        new_password = data.get('new_password', '').strip()
        
        if not uid or not pw_hash or not new_password:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT type FROM user WHERE id = %s", (uid,))
        user = cursor.fetchone()
        
        if not user or user['type'] != 'root':
            cursor.close()
            conn.close()
            return jsonify({'success': False}), 403
        
        if uid == target_uid:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Cannot reset own password via admin'}), 400
        
        cursor.execute("SELECT id FROM user WHERE id = %s", (target_uid,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Target user not found'}), 404
        
        new_pw_hash = hash_password(new_password)
        cursor.execute("UPDATE user SET pwhash = %s WHERE id = %s", (new_pw_hash, target_uid))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Password reset successfully'}), 200
    except Exception as e:
        print(f"Reset password error: {e}")
        return jsonify({'success': False}), 500


@bp.route('/api/admin/user/<int:target_uid>/delete', methods=['POST'])
def api_admin_delete_user(target_uid):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False}), 400
        
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT type FROM user WHERE id = %s", (uid,))
        user = cursor.fetchone()
        
        if not user or user['type'] != 'root':
            cursor.close()
            conn.close()
            return jsonify({'success': False}), 403
        
        if uid == target_uid:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Cannot delete own account'}), 400
        
        cursor.execute("SELECT id FROM user WHERE id = %s", (target_uid,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Target user not found'}), 404
        
        cursor.execute("UPDATE user SET deleted = 1 WHERE id = %s", (target_uid,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'User deleted successfully'}), 200
    except Exception as e:
        print(f"Delete user error: {e}")
        return jsonify({'success': False}), 500


@bp.route('/api/admin/user/<int:target_uid>/restore', methods=['POST'])
def api_admin_restore_user(target_uid):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False}), 400
        
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT type FROM user WHERE id = %s", (uid,))
        user = cursor.fetchone()
        
        if not user or user['type'] != 'root':
            cursor.close()
            conn.close()
            return jsonify({'success': False}), 403
        
        cursor.execute("SELECT id FROM user WHERE id = %s", (target_uid,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Target user not found'}), 404
        
        cursor.execute("UPDATE user SET deleted = 0 WHERE id = %s", (target_uid,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'User restored successfully'}), 200
    except Exception as e:
        print(f"Restore user error: {e}")
        return jsonify({'success': False}), 500
