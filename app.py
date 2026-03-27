import os
import sqlite3
import simplejson as json
from flask import Flask, request, jsonify, send_from_directory
from pusher import Pusher

# Import db setup
from dbsetup import get_db, init_db, get_all_votes

# ============================================
# PUSHER CONFIGURATION - REPLACE THESE VALUES
# ============================================
# Get your credentials from: https://dashboard.pusher.com
PUSHER_APP_ID = '2133420'      
PUSHER_KEY = 'b3376f4c3b42063fadcf'        
PUSHER_SECRET = '318b47f2e59afdf7fc8e'  
PUSHER_CLUSTER = 'ap2'    
# Initialize Pusher client
pusher_client = Pusher(
    app_id=PUSHER_APP_ID,
    key=PUSHER_KEY,
    secret=PUSHER_SECRET,
    cluster=PUSHER_CLUSTER,
    ssl=True
)

app = Flask(__name__)
DATABASE = 'votes.db'

# Default candidates - modify this list or use /api/add-candidate endpoint
DEFAULT_CANDIDATES = ['Candidate A', 'Candidate B', 'Candidate C']


@app.route('/')
def voter_page():
    """Serve the voter page."""
    return send_from_directory('static', 'index.html')


@app.route('/admin')
def admin_page():
    """Serve the admin page."""
    return send_from_directory('static', 'admin.html')


@app.route('/api/names', methods=['GET'])
def get_names():
    """API endpoint to get all names and current votes."""
    return jsonify(get_all_votes())


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get Pusher config for frontend (safe to expose key and cluster)."""
    return jsonify({
        'key': PUSHER_KEY,
        'cluster': PUSHER_CLUSTER
    })


@app.route('/vote', methods=['POST'])
def vote():
    """Handle vote submission and broadcast update."""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    name = data['name']
    
    # Update vote count in database
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if candidate exists
    cursor.execute('SELECT * FROM votes WHERE name = ?', (name,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': f'Candidate "{name}" not found'}), 404
    
    # Increment vote
    cursor.execute(
        'UPDATE votes SET votes = votes + 1 WHERE name = ?',
        (name,)
    )
    conn.commit()
    conn.close()
    
    # Get updated results
    updated_votes = get_all_votes()
    
    # Broadcast to all clients via Pusher
    try:
        pusher_client.trigger('poll', 'vote', updated_votes)
    except Exception as e:
        print(f"Pusher trigger error: {e}")
    
    return jsonify({'success': True, 'data': updated_votes})


@app.route('/api/add-candidate', methods=['POST'])
def add_candidate_endpoint():
    """Add a new candidate dynamically."""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    from dbsetup import add_candidate
    success = add_candidate(data['name'])
    
    if success:
        updated_votes = get_all_votes()
        try:
            pusher_client.trigger('poll', 'vote', updated_votes)
        except Exception as e:
            print(f"Pusher trigger error: {e}")
        return jsonify({'success': True, 'data': updated_votes})
    else:
        return jsonify({'error': 'Candidate already exists'}), 409


@app.route('/api/reset', methods=['POST'])
def reset_votes_endpoint():
    """Reset all votes to zero (admin only)."""
    from dbsetup import reset_votes
    reset_votes()
    updated_votes = get_all_votes()
    
    try:
        pusher_client.trigger('poll', 'vote', updated_votes)
    except Exception as e:
        print(f"Pusher trigger error: {e}")
    
    return jsonify({'success': True, 'data': updated_votes})


@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('static', path)


if __name__ == '__main__':
    # Initialize database with default candidates
    init_db(DEFAULT_CANDIDATES)
    print(f"\nCandidates: {DEFAULT_CANDIDATES}")
    print(f"\nStarting server...")
    print(f"Voter page: http://localhost:5500/")
    print(f"Admin page: http://localhost:5500/admin")
    # Run with threading enabled for Pusher
    app.run(debug=True, host='0.0.0.0', port=5500, threaded=True)

    @app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        'key': PUSHER_KEY,
        'cluster': PUSHER_CLUSTER
    })