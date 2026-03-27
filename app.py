import os
import sqlite3
import simplejson as json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS  # Add this for cross-origin support
from pusher import Pusher

# ============================================
# PUSHER CONFIGURATION - REPLACE THESE
# ============================================
PUSHER_APP_ID = '2133420'
PUSHER_KEY = 'b3376f4c3b42063fadcf'
PUSHER_SECRET = '318b47f2e59afdf7fc8e'
PUSHER_CLUSTER = 'ap2'

pusher_client = Pusher(
    app_id=PUSHER_APP_ID,
    key=PUSHER_KEY,
    secret=PUSHER_SECRET,
    cluster=PUSHER_CLUSTER,
    ssl=True
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains
DATABASE = 'votes.db'

DEFAULT_CANDIDATES = ['Alice', 'Bob', 'Charlie']

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE votes (id INTEGER PRIMARY KEY, name TEXT UNIQUE, votes INTEGER DEFAULT 0)')
    for name in DEFAULT_CANDIDATES:
        cursor.execute('INSERT INTO votes (name, votes) VALUES (?, 0)', (name,))
    conn.commit()
    conn.close()
    print(f"Database initialized with: {DEFAULT_CANDIDATES}")

def get_all_votes():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT name, votes FROM votes ORDER BY name')
    results = [{'name': row['name'], 'votes': row['votes']} for row in cursor.fetchall()]
    conn.close()
    return results

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('static', 'admin.html')

@app.route('/api/names', methods=['GET'])
def get_names():
    return jsonify(get_all_votes())

@app.route('/vote', methods=['POST'])
def vote():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Name required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE votes SET votes = votes + 1 WHERE name = ?', (data['name'],))
    conn.commit()
    conn.close()
    
    updated = get_all_votes()
    pusher_client.trigger('poll', 'vote', updated)
    return jsonify({'success': True, 'data': updated})

@app.route('/api/reset', methods=['POST'])
def reset():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE votes SET votes = 0')
    conn.commit()
    conn.close()
    updated = get_all_votes()
    pusher_client.trigger('poll', 'vote', updated)
    return jsonify({'success': True, 'data': updated})

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    init_db()
    print(f"\nServer running:")
    print(f"  Voter:   http://localhost:5000/")
    print(f"  Admin:   http://localhost:5000/admin")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)