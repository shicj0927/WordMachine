import pymysql
import hashlib
import json
from flask import request


def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='wm',
        password='wm123!@#',
        database='wm',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def check_auth(uid, pw_hash):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE id = %s AND pwhash = %s AND deleted = 0", (uid, pw_hash))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user is not None
    except Exception as e:
        print(f"Database error: {e}")
        return False


def inject_auth_context():
    """Inject authentication status and current user into all templates."""
    try:
        uid = request.cookies.get('uid')
        pwhash = request.cookies.get('pwhash')
        if not uid or not pwhash:
            return {'is_authenticated': False, 'current_user': None}

        try:
            uid_int = int(uid)
        except ValueError:
            return {'is_authenticated': False, 'current_user': None}

        if not check_auth(uid_int, pwhash):
            return {'is_authenticated': False, 'current_user': None}

        # fetch minimal user info
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM user WHERE id = %s AND deleted = 0", (uid_int,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        return {'is_authenticated': True, 'current_user': user}
    except Exception as e:
        print(f"inject_auth_context error: {e}")
        return {'is_authenticated': False, 'current_user': None}
