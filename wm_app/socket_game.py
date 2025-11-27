from . import socketio
from flask_socketio import join_room, leave_room, emit, check_answer
from .utils import get_db_connection, check_auth
import json


def _room_for(game_id):
    return f'game_{game_id}'


def build_game_state(game_id):
    """Return a dict representing the game state suitable for sending to clients."""
    try:
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
            return None

        users_raw = json.loads(game['users']) if game['users'] else []
        wordlist = json.loads(game['wordlist']) if game['wordlist'] else []
        result = json.loads(game['result']) if game['result'] else []

        users_info = []
        for uid in users_raw:
            cursor.execute("SELECT id, username FROM user WHERE id = %s", (uid,))
            u = cursor.fetchone()
            if u:
                users_info.append(u)

        owner_info = None
        if game.get('ownerid'):
            cursor.execute("SELECT id, username FROM user WHERE id = %s", (game['ownerid'],))
            owner_info = cursor.fetchone()

        # Load word details for wordlist
        words_info = []
        for wid in wordlist:
            cursor.execute("SELECT id, english, chinese FROM word WHERE id = %s AND deleted = 0", (wid,))
            w = cursor.fetchone()
            if w:
                words_info.append(w)

        # compute next turn and current index
        current_index = len(result)
        next_turn = None
        next_word = None
        try:
            if users_raw and current_index < len(wordlist):
                next_turn = users_raw[current_index % len(users_raw)]
                next_wid = wordlist[current_index]
                cursor.execute("SELECT id, english, chinese FROM word WHERE id = %s AND deleted = 0", (next_wid,))
                nw = cursor.fetchone()
                if nw:
                    next_word = {'id': nw['id'], 'english': nw['english'], 'chinese': nw['chinese']}
        except Exception:
            next_turn = None
            next_word = None

        cursor.close()
        conn.close()

        return {
            'id': game['id'],
            'dictid': game['dictid'],
            'dictname': game.get('dictname'),
            'users': users_info,
            'words': words_info,
            'result': result,
            'status': game['status'],
            'owner': owner_info,
            'next_turn': next_turn,
            'next_word': next_word,
            'current_index': current_index
        }
    except Exception:
        return None


@socketio.on('game.subscribe')
def handle_subscribe(data):
    """Client asks to subscribe to realtime updates for a game. Does not change DB users list."""
    try:
        uid = int(data.get('uid'))
        pwhash = data.get('pwhash', '').strip()
        game_id = int(data.get('game_id'))
    except Exception:
        return

    if not check_auth(uid, pwhash):
        emit('game.error', {'message': 'Authentication failed'})
        return

    room = _room_for(game_id)
    join_room(room)
    state = build_game_state(game_id)
    if state:
        # send state to the client that subscribed
        emit('game.update', state)


@socketio.on('game.join')
def handle_join(data):
    try:
        uid = int(data.get('uid'))
        pwhash = data.get('pwhash', '').strip()
        game_id = int(data.get('game_id'))
    except Exception:
        emit('game.error', {'message': 'Invalid parameters'})
        return

    if not check_auth(uid, pwhash):
        emit('game.error', {'message': 'Authentication failed'})
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT users, status, result FROM game WHERE id = %s", (game_id,))
    game = cursor.fetchone()
    if not game:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'Game not found'})
        return

    if game['status'] != -1:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'Game already started, cannot join'})
        return

    result_list = json.loads(game['result']) if game['result'] else []
    if result_list:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'Game already finished, cannot join'})
        return

    users = json.loads(game['users']) if game['users'] else []
    if uid in users:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'Already joined'})
        return

    users.append(uid)
    import random
    random.shuffle(users)
    cursor.execute("UPDATE game SET users = %s WHERE id = %s", (json.dumps(users), game_id))
    conn.commit()
    cursor.close()
    conn.close()

    room = _room_for(game_id)
    join_room(room)
    state = build_game_state(game_id)
    # broadcast updated state to the room
    socketio.emit('game.update', state, room=room)


@socketio.on('game.leave')
def handle_leave(data):
    try:
        uid = int(data.get('uid'))
        pwhash = data.get('pwhash', '').strip()
        game_id = int(data.get('game_id'))
    except Exception:
        emit('game.error', {'message': 'Invalid parameters'})
        return

    if not check_auth(uid, pwhash):
        emit('game.error', {'message': 'Authentication failed'})
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT users, status, ownerid FROM game WHERE id = %s", (game_id,))
    game = cursor.fetchone()
    if not game:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'Game not found'})
        return

    if game['status'] != -1:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'Cannot leave started or finished game'})
        return

    users = json.loads(game['users']) if game['users'] else []
    if game.get('ownerid') and uid == game.get('ownerid'):
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'Owner cannot leave the game'})
        return
    if uid not in users:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'Not in game'})
        return

    users.remove(uid)
    cursor.execute("UPDATE game SET users = %s WHERE id = %s", (json.dumps(users), game_id))
    conn.commit()
    cursor.close()
    conn.close()

    room = _room_for(game_id)
    try:
        leave_room(room)
    except Exception:
        pass

    state = build_game_state(game_id)
    socketio.emit('game.update', state, room=room)


@socketio.on('game.start')
def handle_start(data):
    try:
        uid = int(data.get('uid'))
        pwhash = data.get('pwhash', '').strip()
        game_id = int(data.get('game_id'))
    except Exception:
        emit('game.error', {'message': 'Invalid parameters'})
        return

    if not check_auth(uid, pwhash):
        emit('game.error', {'message': 'Authentication failed'})
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT users, status FROM game WHERE id = %s", (game_id,))
    game = cursor.fetchone()
    if not game:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'Game not found'})
        return

    users = json.loads(game['users']) if game['users'] else []
    if uid not in users:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'You must join before starting the game'})
        return

    if len(users) < 2:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'Need at least 2 players to start'})
        return

    cursor.execute("UPDATE game SET status = %s WHERE id = %s", (0, game_id))
    conn.commit()
    cursor.close()
    conn.close()

    room = _room_for(game_id)
    state = build_game_state(game_id)
    socketio.emit('game.update', state, room=room)


@socketio.on('game.answer')
def handle_answer(data):
    try:
        uid = int(data.get('uid'))
        pwhash = data.get('pwhash', '').strip()
        game_id = int(data.get('game_id'))
        word_id = int(data.get('word_id'))
        answer = (data.get('answer') or '').strip().lower()
    except Exception:
        emit('game.error', {'message': 'Invalid parameters'})
        return

    if not check_auth(uid, pwhash):
        emit('game.error', {'message': 'Authentication failed'})
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT users, result, wordlist FROM game WHERE id = %s", (game_id,))
    game = cursor.fetchone()
    if not game:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'Game not found'})
        return

    users = json.loads(game['users']) if game['users'] else []
    if uid not in users:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'Not in game'})
        return

    result = json.loads(game['result']) if game['result'] else []
    wordlist = json.loads(game['wordlist']) if game['wordlist'] else []
    current_index = len(result)

    if current_index >= len(wordlist):
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'All words have been answered'})
        return

    expected_user = users[current_index % len(users)]
    if uid != expected_user:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'Not your turn'})
        return

    expected_word_id = wordlist[current_index]
    if word_id != expected_word_id:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'This is not the expected word for your turn'})
        return

    cursor.execute("SELECT english, chinese FROM word WHERE id = %s AND deleted = 0", (word_id,))
    word = cursor.fetchone()
    if not word:
        cursor.close()
        conn.close()
        emit('game.error', {'message': 'Word not found'})
        return

    is_correct = is_correct = check_answer(answer.strip(), word['english'].strip())

    result.append({
        'uid': uid,
        'word_id': word_id,
        'answer': answer,
        'result': is_correct
    })

    cursor.execute("UPDATE game SET result = %s WHERE id = %s", (json.dumps(result), game_id))
    conn.commit()

    # prepare next turn info
    next_turn = None
    next_word = None
    if len(result) < len(wordlist):
        next_turn = users[len(result) % len(users)]
        next_wid = wordlist[len(result)]
        cursor.execute("SELECT id, english, chinese FROM word WHERE id = %s AND deleted = 0", (next_wid,))
        nw = cursor.fetchone()
        if nw:
            next_word = {'id': nw['id'], 'english': nw['english'], 'chinese': nw['chinese']}

    cursor.close()
    conn.close()

    room = _room_for(game_id)
    # broadcast updated state
    state = build_game_state(game_id)
    socketio.emit('game.update', state, room=room)

    # send a direct ack to the emitter about result
    emit('game.answer_result', {
        'correct': is_correct,
        'expected': word['english'],
        'next_turn': next_turn,
        'next_word': next_word
    })
