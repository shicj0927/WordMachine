from flask import Blueprint, render_template, request, redirect, url_for
from .utils import get_db_connection, check_auth

bp = Blueprint('main', __name__)


@bp.route('/')
def home():
    show_admin_link = False
    try:
        uid = request.cookies.get('uid')
        pwhash = request.cookies.get('pwhash')
        if uid and pwhash:
            try:
                uid_int = int(uid)
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
        show_admin_link = False

    return render_template('home.html', show_admin_link=show_admin_link)


@bp.route('/login/')
def login():
    return render_template('login.html')


@bp.route('/register/')
def register():
    return render_template('register.html')


@bp.route('/changepw/')
def changepw():
    return render_template('changepw.html')


@bp.route('/admin/')
def admin():
    try:
        uid = request.cookies.get('uid')
        pwhash = request.cookies.get('pwhash')
        if not uid or not pwhash:
            return redirect(url_for('main.login'))

        try:
            uid_int = int(uid)
        except ValueError:
            return redirect(url_for('main.login'))

        if not check_auth(uid_int, pwhash):
            return redirect(url_for('main.login'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT type FROM user WHERE id = %s", (uid_int,))
        user = cursor.fetchone()
        users = None
        if user and user.get('type') == 'root':
            cursor.execute("SELECT id, username, introduction, rating, type, deleted FROM user ORDER BY id DESC")
            users = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('admin.html', users=users)
    except Exception as e:
        print(f"Server-side admin render error: {e}")
        return render_template('admin.html', users=None)


@bp.route('/user/<int:profile_id>/')
def user_profile(profile_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, introduction, rating, type FROM user WHERE id = %s AND deleted = 0", (profile_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return redirect(url_for('main.home'))

        return render_template('user.html', user=user)
    except Exception as e:
        print(f"User profile error: {e}")
        return redirect(url_for('main.home'))


@bp.route('/leaderboard/')
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
        return redirect(url_for('main.home'))


@bp.route('/game/<int:game_id>/detail/')
def game_detail(game_id):
    try:
        uid = request.cookies.get('uid')
        pwhash = request.cookies.get('pwhash')
        if not uid or not pwhash:
            return redirect(url_for('main.login'))

        try:
            uid_int = int(uid)
        except ValueError:
            return redirect(url_for('main.login'))

        if not check_auth(uid_int, pwhash):
            return redirect(url_for('main.login'))

        return render_template('game_detail.html')
    except Exception as e:
        print(f"Game detail error: {e}")
        return redirect(url_for('main.home'))


@bp.route('/game/<int:game_id>/')
def game_playing(game_id):
    try:
        uid = request.cookies.get('uid')
        pwhash = request.cookies.get('pwhash')
        if not uid or not pwhash:
            return redirect(url_for('main.login'))

        try:
            uid_int = int(uid)
        except ValueError:
            return redirect(url_for('main.login'))

        if not check_auth(uid_int, pwhash):
            return redirect(url_for('main.login'))

        return render_template('game_playing.html')
    except Exception as e:
        print(f"Game playing error: {e}")
        return redirect(url_for('main.home'))
