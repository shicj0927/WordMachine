from flask import Blueprint, request, jsonify
from .utils import get_db_connection, check_auth
import json
import random

bp = Blueprint('game', __name__)


@bp.route('/api/game/create', methods=['POST'])
def api_game_create():
    try:
        data = request.get_json()
        uid = int(data.get('uid'))
        pw_hash = data.get('pwhash', '').strip()
        dict_id = int(data.get('dict_id'))
        if not uid or not pw_hash or not dict_id:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
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
        
        word_ids = [w['id'] for w in words]
        random.shuffle(word_ids)
        wordlist = json.dumps(word_ids)
        users = json.dumps([uid])

        cursor.execute(
            "INSERT INTO game (dictid, users, wordlist, result, status, ownerid) VALUES (%s, %s, %s, %s, %s, %s)",
            (dict_id, users, wordlist, '[]', -1, uid)
        )
        conn.commit()
        game_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'game_id': game_id, 'message': 'Game created'}), 201
    except Exception as e:
        print(f"Game create error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500


@bp.route('/api/game/list', methods=['GET'])
def api_game_list():
    try:
        uid = request.args.get('uid', type=int)
        pw_hash = request.args.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.id, g.dictid, d.dictname, g.users, g.wordlist, g.result, g.status, g.perf, g.ownerid
            FROM game g
            LEFT JOIN dict d ON g.dictid = d.id
            ORDER BY g.id DESC
        """)
        games = cursor.fetchall()
        
        for game in games:
            user_ids = json.loads(game['users']) if game['users'] else []
            game['wordlist'] = json.loads(game['wordlist']) if game['wordlist'] else []
            game['result'] = json.loads(game['result']) if game['result'] else []
            game['is_joined'] = uid in user_ids

            users_info = []
            for user_id in user_ids:
                cursor.execute("SELECT id, username FROM user WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if user:
                    users_info.append(user)
            game['users'] = users_info

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


@bp.route('/api/game/<int:game_id>', methods=['GET'])
def api_game_get(game_id):
    try:
        uid = request.args.get('uid', type=int)
        pw_hash = request.args.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
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
        
        game['users'] = json.loads(game['users']) if game['users'] else []
        game['wordlist'] = json.loads(game['wordlist']) if game['wordlist'] else []
        game['result'] = json.loads(game['result']) if game['result'] else []

        users_info = []
        for user_id in game['users']:
            cursor.execute("SELECT id, username FROM user WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user:
                users_info.append(user)

        owner_info = None
        if game.get('ownerid'):
            cursor.execute("SELECT id, username FROM user WHERE id = %s", (game['ownerid'],))
            owner_info = cursor.fetchone()

        words_info = []
        for word_id in game['wordlist']:
            cursor.execute("SELECT id, english, chinese FROM word WHERE id = %s AND deleted = 0", (word_id,))
            word = cursor.fetchone()
            if word:
                words_info.append(word)

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

        next_turn_user = None
        next_word_info = None
        try:
            current_index = len(game['result'])
            if game['users'] and current_index < len(game['wordlist']):
                next_turn_user = game['users'][current_index % len(game['users'])]
                next_word_id = game['wordlist'][current_index]
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


@bp.route('/api/game/<int:game_id>/join', methods=['POST'])
def api_game_join(game_id):
    try:
        data = request.get_json()
        uid = int(data.get('uid'))
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT users, status, result FROM game WHERE id = %s", (game_id,))
        game = cursor.fetchone()
        
        if not game:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Game not found'}), 404
        
        if game['status'] != -1:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Game already started, cannot join'}), 400
        
        result = json.loads(game['result']) if game['result'] else []
        if result:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Game already finished, cannot join'}), 400
        
        users = json.loads(game['users']) if game['users'] else []
        if uid in users:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Already joined'}), 400
        
        users.append(uid)
        random.shuffle(users)
        cursor.execute("UPDATE game SET users = %s WHERE id = %s", (json.dumps(users), game_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Joined game'}), 200
    except Exception as e:
        print(f"Game join error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500


@bp.route('/api/game/<int:game_id>/leave', methods=['POST'])
def api_game_leave(game_id):
    try:
        data = request.get_json()
        uid = int(data.get('uid'))
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
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
        
        users = json.loads(game['users']) if game['users'] else []
        if game.get('ownerid') and uid == game.get('ownerid'):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Owner cannot leave the game'}), 400
        if uid not in users:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Not in game'}), 400
        
        users.remove(uid)
        cursor.execute("UPDATE game SET users = %s WHERE id = %s", (json.dumps(users), game_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Left game'}), 200
    except Exception as e:
        print(f"Game leave error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500


@bp.route('/api/game/<int:game_id>/start', methods=['POST'])
def api_game_start(game_id):
    try:
        data = request.get_json()
        uid = int(data.get('uid'))
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT users FROM game WHERE id = %s", (game_id,))
        game = cursor.fetchone()
        
        if not game:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Game not found'}), 404
        
        cursor.execute("UPDATE game SET status = %s WHERE id = %s", (0, game_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Game started'}), 200
    except Exception as e:
        print(f"Game start error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500


@bp.route('/api/game/<int:game_id>/answer', methods=['POST'])
def api_game_answer(game_id):
    try:
        data = request.get_json()
        uid = int(data.get('uid'))
        pw_hash = data.get('pwhash', '').strip()
        word_id = int(data.get('word_id'))
        answer = data.get('answer', '').strip().lower()
        if not uid or not pw_hash or not word_id or not answer:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT users, result, wordlist FROM game WHERE id = %s", (game_id,))
        game = cursor.fetchone()
        if not game:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Game not found'}), 404
        
        users = json.loads(game['users']) if game['users'] else []
        if uid not in users:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Not in game'}), 400

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

        cursor.execute("SELECT english, chinese FROM word WHERE id = %s AND deleted = 0", (word_id,))
        word = cursor.fetchone()
        if not word:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Word not found'}), 404

        is_correct = answer.strip().lower() == word['english'].strip().lower()

        result.append({
            'uid': uid,
            'word_id': word_id,
            'answer': answer,
            'result': is_correct
        })

        cursor.execute("UPDATE game SET result = %s WHERE id = %s", (json.dumps(result), game_id))
        conn.commit()

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


@bp.route('/api/game/<int:game_id>/end', methods=['POST'])
def api_game_end(game_id):
    try:
        data = request.get_json()
        uid = int(data.get('uid'))
        pw_hash = data.get('pwhash', '').strip()
        
        if not uid or not pw_hash:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        if not check_auth(uid, pw_hash):
            return jsonify({'success': False, 'message': 'Authentication failed'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT users, result FROM game WHERE id = %s", (game_id,))
        game = cursor.fetchone()
        
        if not game:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Game not found'}), 404
        
        users = json.loads(game['users']) if game['users'] else []
        if uid not in users:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Not in game'}), 400

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

        for user_id, perf in perf_map.items():
            cursor.execute("SELECT rating FROM user WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user:
                new_rating = user['rating'] + perf
                cursor.execute("UPDATE user SET rating = %s WHERE id = %s", (new_rating, user_id))

        cursor.execute("UPDATE game SET status = %s WHERE id = %s", (1, game_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'perf': perf_map, 'message': 'Game ended and ratings updated'}), 200
    except Exception as e:
        print(f"Game end error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500
