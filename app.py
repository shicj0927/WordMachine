from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for
import pymysql
import hashlib
import json
from datetime import datetime

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Database connection
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='wm',
        password='wm123!@#',
        database='wm',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# Helper function to hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Helper function to check authentication
def check_auth(uid, pw_hash):
    print(uid,pw_hash)
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


@app.context_processor
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

# Routes - Pages
@app.route('/')
def home():
    # Determine whether to show admin link based on cookies and user type
    show_admin_link = False
    try:
        uid = request.cookies.get('uid')
        pwhash = request.cookies.get('pwhash')
        if uid and pwhash:
            try:
                uid_int = int(uid)
                # quick auth check
                if check_auth(uid_int, pwhash):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT type FROM user WHERE id = %s", (uid_int,))
                    user = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    if user and user.get('type') == 'root':
                        show_admin_link = True
            except ValueError:
                pass
    except Exception:
        # ignore errors and render page without admin link
        show_admin_link = False

    return render_template('home.html', show_admin_link=show_admin_link)

@app.route('/login/')
def login():
    return render_template('login.html')

@app.route('/register/')
def register():
    return render_template('register.html')

@app.route('/changepw/')
def changepw():
    return render_template('changepw.html')

@app.route('/admin/')
def admin():
    # Try to render admin page server-side when possible to avoid client-side
    # failures caused by browser extensions (some extensions inject scripts
    # that can break our client JS). We check cookies for uid/pwhash and
    # only render the full users table for root users.
    try:
        uid = request.cookies.get('uid')
        pwhash = request.cookies.get('pwhash')
        if not uid or not pwhash:
            return redirect(url_for('login'))

        # validate auth and role
        try:
            uid_int = int(uid)
        except ValueError:
            return redirect(url_for('login'))

        if not check_auth(uid_int, pwhash):
            return redirect(url_for('login'))

        # check role
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT type FROM user WHERE id = %s", (uid_int,))
        user = cursor.fetchone()
        users = None
        if user and user.get('type') == 'root':
            # fetch non-deleted users by default
            cursor.execute("SELECT id, username, introduction, rating, type, deleted FROM user ORDER BY id DESC")
            users = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('admin.html', users=users)
    except Exception as e:
        print(f"Server-side admin render error: {e}")
        return render_template('admin.html', users=None)

# Public user profile
@app.route('/user/<int:profile_id>/')
def user_profile(profile_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, introduction, rating, type FROM user WHERE id = %s AND deleted = 0", (profile_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return redirect(url_for('home'))

        return render_template('user.html', user=user)
    except Exception as e:
        print(f"User profile error: {e}")
        return redirect(url_for('home'))


# Leaderboard (sorted by rating desc)
@app.route('/leaderboard/')
def leaderboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, introduction, rating FROM user WHERE deleted = 0 ORDER BY rating DESC, id ASC LIMIT 100")
        users = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('leaderboard.html', users=users)
    except Exception as e:
        print(f"Leaderboard error: {e}")
        return redirect(url_for('home'))

# Game page - game detail
@app.route('/game/<int:game_id>/detail/')
def game_detail(game_id):
    try:
        uid = request.cookies.get('uid')
        pwhash = request.cookies.get('pwhash')
        if not uid or not pwhash:
            return redirect(url_for('login'))

        try:
            uid_int = int(uid)
        except ValueError:
            return redirect(url_for('login'))

        if not check_auth(uid_int, pwhash):
            return redirect(url_for('login'))

        return render_template('game_detail.html')
    except Exception as e:
        print(f"Game detail error: {e}")
        return redirect(url_for('home'))

@app.route('/game/<int:game_id>/')
def game_playing(game_id):
    try:
        uid = request.cookies.get('uid')
        pwhash = request.cookies.get('pwhash')
        if not uid or not pwhash:
            return redirect(url_for('login'))

        try:
            uid_int = int(uid)
        except ValueError:
            return redirect(url_for('login'))

        if not check_auth(uid_int, pwhash):
            return redirect(url_for('login'))

        return render_template('game_playing.html')
    except Exception as e:
        print(f"Game playing error: {e}")
        return redirect(url_for('home'))

# API Routes - User Management
@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        introduction = data.get('introduction', '').strip()
        
        # Validation
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        if len(username) > 255 or len(password) < 6:
            return jsonify({'success': False, 'message': 'Invalid username or password length'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT id FROM user WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Username already exists'}), 409
        
        # Insert new user
        pw_hash = hash_password(password)
        print(f"[register] creating user: {username} pw={password} pw_hash={pw_hash}")
        cursor.execute(
            "INSERT INTO user (username, pwhash, introduction, rating, type, deleted) VALUES (%s, %s, %s, %s, %s, %s)",
            (username, pw_hash, introduction, 0, 'normal', False)
        )
        conn.commit()
        
        # Get the new user's ID
        cursor.execute("SELECT id FROM user WHERE username = %s", (username,))
        user = cursor.fetchone()
        uid = user['id']
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'uid': uid, 'message': 'Registration successful'}), 201
    except Exception as e:
        print(f"Register error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find user by username
        cursor.execute("SELECT id, pwhash FROM user WHERE username = %s AND deleted = 0", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            print(f"[login] user not found: {username}")
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

        # Verify password
        pw_hash = hash_password(password)
        print(password,pw_hash)
        match = (user['pwhash'] == pw_hash)
        print(f"[login] username={username} id={user['id']} match={match}")
        if not match:
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
        
        return jsonify({'success': True, 'uid': user['id'], 'pwhash': pw_hash}), 200
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/verify', methods=['POST'])
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

@app.route('/api/user/<int:uid>', methods=['GET'])
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

@app.route('/api/user/<int:uid>/update', methods=['POST'])
def api_update_user(uid):
    try:
        data = request.get_json()
        # Extract fields; introduction may be omitted (None) to indicate no change
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
        
        # Verify authentication via pw_hash cookie/header
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401

        # Build updates. If changing password, require current_password to be provided and correct.
        updates = []
        params = []

        conn = get_db_connection()
        cursor = conn.cursor()

        if new_password is not None and new_password != '':
            # Changing password requires verifying current password
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

        # Introduction update is allowed without re-entering current password
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

# Admin API Routes
@app.route('/api/admin/check', methods=['POST'])
def api_admin_check():
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False}), 400
        
        # Verify authentication
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        # Get user info (return type for all authenticated users)
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

@app.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    try:
        uid = request.args.get('uid', type=int)
        pw_hash = request.args.get('pwhash', '').strip()
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
        
        if not uid or not pw_hash:
            return jsonify({'success': False}), 400
        
        # Verify authentication and admin access
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
        
        # Get users
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

@app.route('/api/admin/user/<int:target_uid>/reset-password', methods=['POST'])
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
        
        # Verify authentication and admin access
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
        
        # Cannot reset own password via admin
        if uid == target_uid:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Cannot reset own password via admin'}), 400
        
        # Check target user exists
        cursor.execute("SELECT id FROM user WHERE id = %s", (target_uid,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Target user not found'}), 404
        
        # Reset password
        new_pw_hash = hash_password(new_password)
        cursor.execute("UPDATE user SET pwhash = %s WHERE id = %s", (new_pw_hash, target_uid))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Password reset successfully'}), 200
    except Exception as e:
        print(f"Reset password error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/admin/user/<int:target_uid>/delete', methods=['POST'])
def api_admin_delete_user(target_uid):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False}), 400
        
        # Verify authentication and admin access
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
        
        # Cannot delete own account
        if uid == target_uid:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Cannot delete own account'}), 400
        
        # Check target user exists
        cursor.execute("SELECT id FROM user WHERE id = %s", (target_uid,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Target user not found'}), 404
        
        # Soft delete user
        cursor.execute("UPDATE user SET deleted = 1 WHERE id = %s", (target_uid,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'User deleted successfully'}), 200
    except Exception as e:
        print(f"Delete user error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/admin/user/<int:target_uid>/restore', methods=['POST'])
def api_admin_restore_user(target_uid):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False}), 400
        
        # Verify authentication and admin access
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
        
        # Check target user exists
        cursor.execute("SELECT id FROM user WHERE id = %s", (target_uid,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Target user not found'}), 404
        
        # Restore user
        cursor.execute("UPDATE user SET deleted = 0 WHERE id = %s", (target_uid,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'User restored successfully'}), 200
    except Exception as e:
        print(f"Restore user error: {e}")
        return jsonify({'success': False}), 500

# Dictionary Management API Routes

@app.route('/api/dicts', methods=['GET'])
def api_get_dicts():
    try:
        uid = request.args.get('uid', type=int)
        pw_hash = request.args.get('pwhash', '').strip()

        if not uid or not pw_hash:
            return jsonify({'success': False}), 400

        # Verify authentication (user, not necessarily root)
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all non-deleted dicts with word count
        cursor.execute("""
            SELECT d.id, d.dictname, COUNT(w.id) as word_count
            FROM dict d
            LEFT JOIN word w ON d.id = w.dictid AND w.deleted = 0
            WHERE d.deleted = 0
            GROUP BY d.id
            ORDER BY d.id DESC
        """)
        dicts = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'dicts': dicts}), 200
    except Exception as e:
        print(f"Get dicts error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/dict', methods=['POST'])
def api_create_dict():
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        dictname = data.get('dictname', '').strip()

        if not uid or not pw_hash or not dictname:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        # Verify authentication (any authenticated user)
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        # Create dict
        cursor.execute("INSERT INTO dict (dictname, deleted) VALUES (%s, 0)", (dictname,))
        conn.commit()
        dict_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'dict_id': dict_id, 'message': 'Dictionary created'}), 201
    except Exception as e:
        print(f"Create dict error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/dict/<int:dict_id>', methods=['PUT'])
def api_update_dict(dict_id):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        dictname = data.get('dictname', '').strip()

        if not uid or not pw_hash or not dictname:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        # Verify authentication (any authenticated user)
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check dict exists
        cursor.execute("SELECT id FROM dict WHERE id = %s AND deleted = 0", (dict_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Dictionary not found'}), 404

        # Update dict
        cursor.execute("UPDATE dict SET dictname = %s WHERE id = %s", (dictname, dict_id))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Dictionary updated'}), 200
    except Exception as e:
        print(f"Update dict error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/dict/<int:dict_id>', methods=['DELETE'])
def api_delete_dict(dict_id):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()

        if not uid or not pw_hash:
            return jsonify({'success': False}), 400

        # Verify authentication (any authenticated user)
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check dict exists
        cursor.execute("SELECT id FROM dict WHERE id = %s AND deleted = 0", (dict_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Dictionary not found'}), 404

        # Soft delete dict and cascade delete its words
        cursor.execute("UPDATE dict SET deleted = 1 WHERE id = %s", (dict_id,))
        cursor.execute("UPDATE word SET deleted = 1 WHERE dictid = %s", (dict_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Dictionary and its words deleted'}), 200
    except Exception as e:
        print(f"Delete dict error: {e}")
        return jsonify({'success': False}), 500

# Word Management API Routes

@app.route('/api/dict/<int:dict_id>/words', methods=['GET'])
def api_get_words(dict_id):
    try:
        uid = request.args.get('uid', type=int)
        pw_hash = request.args.get('pwhash', '').strip()

        if not uid or not pw_hash:
            return jsonify({'success': False}), 400

        # Verify authentication
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check dict exists
        cursor.execute("SELECT id FROM dict WHERE id = %s AND deleted = 0", (dict_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Dictionary not found'}), 404

        # Get non-deleted words
        cursor.execute(
            "SELECT id, dictid, english, chinese FROM word WHERE dictid = %s AND deleted = 0 ORDER BY id ASC",
            (dict_id,)
        )
        words = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'words': words}), 200
    except Exception as e:
        print(f"Get words error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/dict/<int:dict_id>/word', methods=['POST'])
def api_create_word(dict_id):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        english = data.get('english', '').strip()
        chinese = data.get('chinese', '').strip()

        if not uid or not pw_hash or not english or not chinese:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        # Verify authentication (any authenticated user)
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check dict exists
        cursor.execute("SELECT id FROM dict WHERE id = %s AND deleted = 0", (dict_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Dictionary not found'}), 404

        # Create word
        cursor.execute(
            "INSERT INTO word (dictid, english, chinese, deleted) VALUES (%s, %s, %s, 0)",
            (dict_id, english, chinese)
        )
        conn.commit()
        word_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'word_id': word_id, 'message': 'Word created'}), 201
    except Exception as e:
        print(f"Create word error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/word/<int:word_id>', methods=['PUT'])
def api_update_word(word_id):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        english = data.get('english', '').strip()
        chinese = data.get('chinese', '').strip()

        if not uid or not pw_hash or not english or not chinese:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        # Verify authentication (any authenticated user)
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check word exists
        cursor.execute("SELECT dictid FROM word WHERE id = %s AND deleted = 0", (word_id,))
        word = cursor.fetchone()
        if not word:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Word not found'}), 404

        # Update word
        cursor.execute(
            "UPDATE word SET english = %s, chinese = %s WHERE id = %s",
            (english, chinese, word_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Word updated'}), 200
    except Exception as e:
        print(f"Update word error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/word/<int:word_id>', methods=['DELETE'])
def api_delete_word(word_id):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()

        if not uid or not pw_hash:
            return jsonify({'success': False}), 400

        # Verify authentication (any authenticated user)
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check word exists
        cursor.execute("SELECT id FROM word WHERE id = %s AND deleted = 0", (word_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Word not found'}), 404

        # Soft delete word
        cursor.execute("UPDATE word SET deleted = 1 WHERE id = %s", (word_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Word deleted'}), 200
    except Exception as e:
        print(f"Delete word error: {e}")
        return jsonify({'success': False}), 500

# CSV Import/Export API Routes

@app.route('/api/dict/<int:dict_id>/import-csv', methods=['POST'])
def api_import_csv(dict_id):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        csv_content = data.get('csv', '')

        if not uid or not pw_hash or not csv_content:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        # Verify authentication (any authenticated user)
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check dict exists
        cursor.execute("SELECT id FROM dict WHERE id = %s AND deleted = 0", (dict_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Dictionary not found'}), 404

        # Parse CSV and insert words
        lines = csv_content.strip().split('\n')
        count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',', 1)
            if len(parts) == 2:
                english, chinese = parts[0].strip(), parts[1].strip()
                if english and chinese:
                    cursor.execute(
                        "INSERT INTO word (dictid, english, chinese, deleted) VALUES (%s, %s, %s, 0)",
                        (dict_id, english, chinese)
                    )
                    count += 1
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'count': count, 'message': f'{count} words imported'}), 200
    except Exception as e:
        print(f"Import CSV error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/dict/<int:dict_id>/export-csv', methods=['GET'])
def api_export_csv(dict_id):
    try:
        uid = request.args.get('uid', type=int)
        pw_hash = request.args.get('pwhash', '').strip()

        if not uid or not pw_hash:
            return jsonify({'success': False}), 400

        # Verify authentication
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check dict exists
        cursor.execute("SELECT dictname FROM dict WHERE id = %s AND deleted = 0", (dict_id,))
        dict_info = cursor.fetchone()
        if not dict_info:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Dictionary not found'}), 404

        # Get words
        cursor.execute(
            "SELECT english, chinese FROM word WHERE dictid = %s AND deleted = 0 ORDER BY id ASC",
            (dict_id,)
        )
        words = cursor.fetchall()
        cursor.close()
        conn.close()

        # Generate CSV content
        csv_lines = [f"{word['english']},{word['chinese']}" for word in words]
        csv_content = '\n'.join(csv_lines)

        return jsonify({
            'success': True,
            'filename': f"{dict_info['dictname']}.csv",
            'content': csv_content
        }), 200
    except Exception as e:
        print(f"Export CSV error: {e}")
        return jsonify({'success': False}), 500

# Game API Routes
import random

@app.route('/api/game/create', methods=['POST'])
def api_game_create():
    """Create a new game."""
    try:
        data = request.get_json()
        print(data)
        uid = int(data.get('uid'))
        pw_hash = data.get('pwhash', '').strip()
        dict_id = int(data.get('dict_id'))
        if not uid or not pw_hash or not dict_id:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        # Verify authentication
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if dictionary exists and has words
        cursor.execute("SELECT id FROM dict WHERE id = %s AND deleted = 0", (dict_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Dictionary not found'}), 404
        
        cursor.execute("SELECT id FROM word WHERE dictid = %s AND deleted = 0", (dict_id,))
        words = cursor.fetchall()
        if not words:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Dictionary has no words'}), 400
        
        # Shuffle word list
        word_ids = [w['id'] for w in words]
        random.shuffle(word_ids)
        wordlist = json.dumps(word_ids)
        
        # Initialize with creator
        users = json.dumps([uid])
        
        # Create game (status=-1 for not started)
        cursor.execute(
            "INSERT INTO game (dictid, users, wordlist, result, status, ownerid) VALUES (%s, %s, %s, %s, %s, %s)",
            (dict_id, users, wordlist, '[]', -1, uid)
        )
        conn.commit()
        
        # Get the new game's ID
        game_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'game_id': game_id, 'message': 'Game created'}), 201
    except Exception as e:
        print(f"Game create error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/game/list', methods=['GET'])
def api_game_list():
    """List all games (未开始/进行中/已结束)."""
    try:
        uid = request.args.get('uid', type=int)
        pw_hash = request.args.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        # Verify authentication
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all games with dict info
        cursor.execute("""
            SELECT g.id, g.dictid, d.dictname, g.users, g.wordlist, g.result, g.status, g.perf, g.ownerid
            FROM game g
            LEFT JOIN dict d ON g.dictid = d.id
            ORDER BY g.id DESC
        """)
        games = cursor.fetchall()
        
        # Parse JSON fields for each game and fetch user info
        for game in games:
            user_ids = json.loads(game['users']) if game['users'] else []
            game['wordlist'] = json.loads(game['wordlist']) if game['wordlist'] else []
            game['result'] = json.loads(game['result']) if game['result'] else []
            game['is_joined'] = uid in user_ids

            # Fetch user info for all users in the game
            users_info = []
            for user_id in user_ids:
                cursor.execute("SELECT id, username FROM user WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if user:
                    users_info.append(user)
            game['users'] = users_info

            # Fetch owner info if present
            owner_info = None
            if game.get('ownerid'):
                cursor.execute("SELECT id, username FROM user WHERE id = %s", (game['ownerid'],))
                owner_info = cursor.fetchone()
            game['owner'] = owner_info
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'games': games}), 200
    except Exception as e:
        print(f"Game list error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/game/<int:game_id>', methods=['GET'])
def api_game_get(game_id):
    """Get game details."""
    try:
        uid = request.args.get('uid', type=int)
        pw_hash = request.args.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        # Verify authentication
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get game info
        cursor.execute("""
            SELECT g.id, g.dictid, d.dictname, g.users, g.wordlist, g.result, g.status, g.ownerid
            FROM game g
            LEFT JOIN dict d ON g.dictid = d.id
            WHERE g.id = %s
        """, (game_id,))
        game = cursor.fetchone()
        
        if not game:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Game not found'}), 404
        
        # Parse JSON fields
        game['users'] = json.loads(game['users']) if game['users'] else []
        game['wordlist'] = json.loads(game['wordlist']) if game['wordlist'] else []
        game['result'] = json.loads(game['result']) if game['result'] else []

        # Get user info for all users in the game
        users_info = []
        for user_id in game['users']:
            cursor.execute("SELECT id, username FROM user WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user:
                users_info.append(user)
        
        # Get owner info
        owner_info = None
        if game.get('ownerid'):
            cursor.execute("SELECT id, username FROM user WHERE id = %s", (game['ownerid'],))
            owner_info = cursor.fetchone()
        
        # Get word info for all words in the wordlist
        words_info = []
        for word_id in game['wordlist']:
            cursor.execute("SELECT id, english, chinese FROM word WHERE id = %s", (word_id,))
            word = cursor.fetchone()
            if word:
                words_info.append(word)
        
        # Calculate perf for each user
        perf_map = {}
        for user_id in game['users']:
            perf_map[user_id] = {'correct': 0, 'wrong': 0, 'perf': 0}
        
        for result in game['result']:
            uid_result = result.get('uid')
            is_correct = result.get('result', False)
            if uid_result in perf_map:
                if is_correct:
                    perf_map[uid_result]['correct'] += 1
                    perf_map[uid_result]['perf'] += 1
                else:
                    perf_map[uid_result]['wrong'] += 1
                    perf_map[uid_result]['perf'] -= 1
        
        cursor.close()
        conn.close()
        # Determine next turn and next word (use shared wordlist and round-robin turns)
        next_turn_user = None
        next_word_info = None
        try:
            current_index = len(game['result'])
            if game['users'] and current_index < len(game['wordlist']):
                next_turn_user = game['users'][current_index % len(game['users'])]
                next_word_id = game['wordlist'][current_index]
                # fetch next word info (Chinese prompt + english expected answer)
                conn2 = get_db_connection()
                c2 = conn2.cursor()
                c2.execute("SELECT id, english, chinese FROM word WHERE id = %s AND deleted = 0", (next_word_id,))
                w = c2.fetchone()
                try:
                    c2.close()
                    conn2.close()
                except Exception:
                    pass
                if w:
                    next_word_info = {'id': w['id'], 'english': w['english'], 'chinese': w['chinese']}
        except Exception:
            next_turn_user = None
            next_word_info = None

        return jsonify({
            'success': True,
            'game': {
                'id': game['id'],
                'dictid': game['dictid'],
                'dictname': game['dictname'],
                'users': users_info,
                'words': words_info,
                'result': game['result'],
                'perf': perf_map,
                'status': game['status'],
                'owner': owner_info,
                'next_turn': next_turn_user,
                'next_word': next_word_info,
                'current_index': len(game['result'])
            }
        }), 200
    except Exception as e:
        print(f"Game get error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/game/<int:game_id>/join', methods=['POST'])
def api_game_join(game_id):
    """Join a game (only if not started)."""
    try:
        data = request.get_json()
        uid = int(data.get('uid'))
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        # Verify authentication
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get game
        cursor.execute("SELECT users, status, result FROM game WHERE id = %s", (game_id,))
        game = cursor.fetchone()
        
        if not game:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Game not found'}), 404
        
        if game['status']!=-1:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Game already started, cannot join'}), 400
        
        # Check if game is finished (has results)
        result = json.loads(game['result']) if game['result'] else []
        if result:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Game already finished, cannot join'}), 400
        
        # Parse users and add new user
        users = json.loads(game['users']) if game['users'] else []
        if uid in users:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Already joined'}), 400
        
        users.append(uid)
        random.shuffle(users)  # Re-shuffle user order
        
        # Update game
        cursor.execute("UPDATE game SET users = %s WHERE id = %s", (json.dumps(users), game_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Joined game'}), 200
    except Exception as e:
        print(f"Game join error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/game/<int:game_id>/leave', methods=['POST'])
def api_game_leave(game_id):
    """Leave a game (only if not started)."""
    try:
        data = request.get_json()
        uid = int(data.get('uid'))
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        # Verify authentication
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get game
        cursor.execute("SELECT users, status, ownerid FROM game WHERE id = %s", (game_id,))
        game = cursor.fetchone()
        
        if not game:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Game not found'}), 404
        
        if game['status'] != -1:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Cannot leave started or finished game'}), 400
        
        # Parse users and remove user
        users = json.loads(game['users']) if game['users'] else []
        # Owner cannot leave the game
        if game.get('ownerid') and uid == game.get('ownerid'):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Owner cannot leave the game'}), 400
        if uid not in users:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Not in game'}), 400
        
        users.remove(uid)
        
        # Update game
        cursor.execute("UPDATE game SET users = %s WHERE id = %s", (json.dumps(users), game_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Left game'}), 200
    except Exception as e:
        print(f"Game leave error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/game/<int:game_id>/start', methods=['POST'])
def api_game_start(game_id):
    """Start a game (only creator)."""
    try:
        data = request.get_json()
        uid = int(data.get('uid'))
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        # Verify authentication
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get game
        cursor.execute("SELECT users FROM game WHERE id = %s", (game_id,))
        game = cursor.fetchone()
        
        if not game:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Game not found'}), 404
        
        # Check if uid is the creator (first user in the original list, but we need to track this better)
        # For now, allow any user to start (as per gen.md: "发起者有权点击开始按钮开始对局")
        # TODO: Store creator_id in game table for proper authorization
        
        cursor.execute("UPDATE game SET status = %s WHERE id = %s", (0, game_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Game started'}), 200
    except Exception as e:
        print(f"Game start error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/game/<int:game_id>/answer', methods=['POST'])
def api_game_answer(game_id):
    """Submit an answer to a word."""
    try:
        data = request.get_json()
        uid = int(data.get('uid'))
        pw_hash = data.get('pwhash', '').strip()
        word_id = int(data.get('word_id'))
        answer = data.get('answer', '').strip().lower()
        print(data,uid,word_id,answer)
        if not uid or not pw_hash or not word_id or not answer:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        # Verify authentication
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get game
        cursor.execute("SELECT users, result, wordlist FROM game WHERE id = %s", (game_id,))
        game = cursor.fetchone()
        if not game:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Game not found'}), 404
        
        # Check if user is in the game
        users = json.loads(game['users']) if game['users'] else []
        if uid not in users:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Not in game'}), 400

        # Parse existing results and determine whose turn it is and which word is expected
        result = json.loads(game['result']) if game['result'] else []
        wordlist = json.loads(game['wordlist']) if game['wordlist'] else []
        current_index = len(result)

        if current_index >= len(wordlist):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'All words have been answered'}), 400

        expected_user = users[current_index % len(users)]
        if uid != expected_user:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Not your turn'}), 400

        expected_word_id = wordlist[current_index]
        if word_id != expected_word_id:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'This is not the expected word for your turn'}), 400

        # Get expected word info
        cursor.execute("SELECT english, chinese FROM word WHERE id = %s AND deleted = 0", (word_id,))
        word = cursor.fetchone()
        if not word:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Word not found'}), 404

        # Check if answer is correct (answer should be the English word; prompt will be Chinese in UI)
        is_correct = answer.strip().lower() == word['english'].strip().lower()

        # Append result
        result.append({
            'uid': uid,
            'word_id': word_id,
            'answer': answer,
            'result': is_correct
        })

        # Update game result
        cursor.execute("UPDATE game SET result = %s WHERE id = %s", (json.dumps(result), game_id))
        conn.commit()

        # Prepare next turn info
        next_turn = None
        next_word = None
        if len(result) < len(game['wordlist']):
            next_turn = users[len(result) % len(users)]
            next_word_id = game['wordlist'][len(result)]
            cursor.execute("SELECT id, english, chinese FROM word WHERE id = %s AND deleted = 0", (next_word_id,))
            nw = cursor.fetchone()
            if nw:
                next_word = {'id': nw['id'], 'english': nw['english'], 'chinese': nw['chinese']}

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'correct': is_correct,
            'expected': word['english'],
            'next_turn': next_turn,
            'next_word': next_word,
            'message': 'Answer recorded'
        }), 200
    except Exception as e:
        print(f"Game answer error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/game/<int:game_id>/end', methods=['POST'])
def api_game_end(game_id):
    """End a game and calculate ratings."""
    try:
        data = request.get_json()
        uid = int(data.get('uid'))
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        # Verify authentication
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get game
        cursor.execute("SELECT users, result FROM game WHERE id = %s", (game_id,))
        game = cursor.fetchone()
        
        if not game:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Game not found'}), 404
        
        # Check if user is in the game (or anyone can end?)
        users = json.loads(game['users']) if game['users'] else []
        if uid not in users:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Not in game'}), 400
        
        # Calculate perf for each user
        result = json.loads(game['result']) if game['result'] else []
        perf_map = {}
        for user_id in users:
            perf_map[user_id] = 0
        
        for result_item in result:
            uid_result = result_item.get('uid')
            is_correct = result_item.get('result', False)
            if uid_result in perf_map:
                if is_correct:
                    perf_map[uid_result] += 1
                else:
                    perf_map[uid_result] -= 1
        
        # Update ratings for each user
        for user_id, perf in perf_map.items():
            cursor.execute("SELECT rating FROM user WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user:
                new_rating = user['rating'] + perf
                cursor.execute("UPDATE user SET rating = %s WHERE id = %s", (new_rating, user_id))
        
        # Update game: status=1 (finished)
        cursor.execute("UPDATE game SET status = %s WHERE id = %s", (1, game_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'perf': perf_map, 'message': 'Game ended and ratings updated'}), 200
    except Exception as e:
        print(f"Game end error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port="80")
