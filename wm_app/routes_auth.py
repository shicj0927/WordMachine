from flask import Blueprint, request, jsonify
from .utils import get_db_connection, hash_password, check_auth

bp = Blueprint('auth', __name__)


@bp.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        introduction = data.get('introduction', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        if len(username) > 255 or len(password) < 6:
            return jsonify({'success': False, 'message': 'Invalid username or password length'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM user WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Username already exists'}), 409
        
        pw_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO user (username, pwhash, introduction, rating, type, deleted) VALUES (%s, %s, %s, %s, %s, %s)",
            (username, pw_hash, introduction, 0, 'normal', False)
        )
        conn.commit()
        cursor.execute("SELECT id FROM user WHERE username = %s", (username,))
        user = cursor.fetchone()
        uid = user['id']
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'uid': uid, 'message': 'Registration successful'}), 201
    except Exception as e:
        print(f"Register error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500


@bp.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, pwhash FROM user WHERE username = %s AND deleted = 0", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

        pw_hash = hash_password(password)
        if user['pwhash'] != pw_hash:
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
        
        return jsonify({'success': True, 'uid': user['id'], 'pwhash': pw_hash}), 200
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500


@bp.route('/api/verify', methods=['POST'])
def api_verify():
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False}), 400
        
        if check_auth(uid, pw_hash):
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False}), 401
    except Exception as e:
        print(f"Verify error: {e}")
        return jsonify({'success': False}), 500


@bp.route('/api/user/<int:uid>', methods=['GET'])
def api_get_user(uid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, introduction, rating, type FROM user WHERE id = %s AND deleted = 0", (uid,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return jsonify({'success': True, 'user': user}), 200
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500


@bp.route('/api/user/<int:uid>/update', methods=['POST'])
def api_update_user(uid):
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        if current_password is not None:
            current_password = current_password.strip()
        new_password = data.get('new_password')
        if new_password is not None:
            new_password = new_password.strip()
        introduction = data.get('introduction')
        if introduction is not None:
            introduction = introduction.strip()
        pw_hash = data.get('pwhash', '').strip()
        
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401

        updates = []
        params = []

        conn = get_db_connection()
        cursor = conn.cursor()

        if new_password is not None and new_password != '':
            cursor.execute("SELECT pwhash FROM user WHERE id = %s", (uid,))
            user = cursor.fetchone()
            if not user or current_password is None or user['pwhash'] != hash_password(current_password):
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Current password incorrect'}), 401

            if len(new_password) < 6:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': 'New password must be at least 6 characters'}), 400

            updates.append("pwhash = %s")
            params.append(hash_password(new_password))

        if introduction is not None:
            updates.append("introduction = %s")
            params.append(introduction)

        if not updates:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'No updates provided'}), 400

        params.append(uid)
        query = "UPDATE user SET " + ", ".join(updates) + " WHERE id = %s"
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'User updated successfully'}), 200
    except Exception as e:
        print(f"Update user error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500
