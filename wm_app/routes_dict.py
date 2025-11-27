from flask import Blueprint, request, jsonify
from .utils import get_db_connection, check_auth
import json

bp = Blueprint('dicts', __name__)


@bp.route('/api/dicts', methods=['GET'])
def api_get_dicts():
    try:
        uid = request.args.get('uid', type=int)
        pw_hash = request.args.get('pwhash', '').strip()

        if not uid or not pw_hash:
            return jsonify({'success': False}), 400

        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
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


@bp.route('/api/dict', methods=['POST'])
def api_create_dict():
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        dictname = data.get('dictname', '').strip()

        if not uid or not pw_hash or not dictname:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO dict (dictname, deleted) VALUES (%s, 0)", (dictname,))
        conn.commit()
        dict_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'dict_id': dict_id, 'message': 'Dictionary created'}), 201
    except Exception as e:
        print(f"Create dict error: {e}")
        return jsonify({'success': False}), 500


@bp.route('/api/dict/<int:dict_id>', methods=['PUT'])
def api_update_dict(dict_id):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        dictname = data.get('dictname', '').strip()

        if not uid or not pw_hash or not dictname:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM dict WHERE id = %s AND deleted = 0", (dict_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Dictionary not found'}), 404

        cursor.execute("UPDATE dict SET dictname = %s WHERE id = %s", (dictname, dict_id))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Dictionary updated'}), 200
    except Exception as e:
        print(f"Update dict error: {e}")
        return jsonify({'success': False}), 500


@bp.route('/api/dict/<int:dict_id>', methods=['DELETE'])
def api_delete_dict(dict_id):
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
        cursor.execute("SELECT id FROM dict WHERE id = %s AND deleted = 0", (dict_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Dictionary not found'}), 404

        cursor.execute("UPDATE dict SET deleted = 1 WHERE id = %s", (dict_id,))
        cursor.execute("UPDATE word SET deleted = 1 WHERE dictid = %s", (dict_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Dictionary and its words deleted'}), 200
    except Exception as e:
        print(f"Delete dict error: {e}")
        return jsonify({'success': False}), 500


@bp.route('/api/dict/<int:dict_id>/words', methods=['GET'])
def api_get_words(dict_id):
    try:
        uid = request.args.get('uid', type=int)
        pw_hash = request.args.get('pwhash', '').strip()

        if not uid or not pw_hash:
            return jsonify({'success': False}), 400

        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM dict WHERE id = %s AND deleted = 0", (dict_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Dictionary not found'}), 404

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


@bp.route('/api/dict/<int:dict_id>/word', methods=['POST'])
def api_create_word(dict_id):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        english = data.get('english', '').strip()
        chinese = data.get('chinese', '').strip()

        if not uid or not pw_hash or not english or not chinese:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM dict WHERE id = %s AND deleted = 0", (dict_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Dictionary not found'}), 404

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


@bp.route('/api/word/<int:word_id>', methods=['PUT'])
def api_update_word(word_id):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        english = data.get('english', '').strip()
        chinese = data.get('chinese', '').strip()

        if not uid or not pw_hash or not english or not chinese:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT dictid FROM word WHERE id = %s AND deleted = 0", (word_id,))
        word = cursor.fetchone()
        if not word:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Word not found'}), 404

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

def erase_marks(s):
    if s[0]=='"':
        s=s[1:]
    if s[len(s)-1]=='"':
        s=s[:-1]
    return s

@bp.route('/api/word/<int:word_id>', methods=['DELETE'])
def api_delete_word(word_id):
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
        cursor.execute("SELECT id FROM word WHERE id = %s AND deleted = 0", (word_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Word not found'}), 404

        cursor.execute("UPDATE word SET deleted = 1 WHERE id = %s", (word_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Word deleted'}), 200
    except Exception as e:
        print(f"Delete word error: {e}")
        return jsonify({'success': False}), 500


@bp.route('/api/dict/<int:dict_id>/import-csv', methods=['POST'])
def api_import_csv(dict_id):
    try:
        data = request.get_json()
        uid = data.get('uid')
        pw_hash = data.get('pwhash', '').strip()
        csv_content = data.get('csv', '')

        if not uid or not pw_hash or not csv_content:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM dict WHERE id = %s AND deleted = 0", (dict_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Dictionary not found'}), 404

        lines = csv_content.strip().split('\n')
        count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',', 1)
            if len(parts) == 2:
                english, chinese = erase_marks(parts[0].strip()), erase_marks(parts[1].strip())
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


@bp.route('/api/dict/<int:dict_id>/export-csv', methods=['GET'])
def api_export_csv(dict_id):
    try:
        uid = request.args.get('uid', type=int)
        pw_hash = request.args.get('pwhash', '').strip()

        if not uid or not pw_hash:
            return jsonify({'success': False}), 400

        if not check_auth(uid, pw_hash):
            return jsonify({'success': False}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT dictname FROM dict WHERE id = %s AND deleted = 0", (dict_id,))
        dict_info = cursor.fetchone()
        if not dict_info:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Dictionary not found'}), 404

        cursor.execute(
            "SELECT english, chinese FROM word WHERE dictid = %s AND deleted = 0 ORDER BY id ASC",
            (dict_id,)
        )
        words = cursor.fetchall()
        cursor.close()
        conn.close()

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
