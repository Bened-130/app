import os
import sqlite3

DATABASE = 'votes.db'

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(candidate_names=None):
    """
    Initialize database with votes table and seed data.
    
    Args:
        candidate_names: List of names to initialize. If None, uses defaults.
    """
    # Remove existing database to start fresh
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print(f"Removed existing database: {DATABASE}")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            votes INTEGER DEFAULT 0
        )
    ''')
    
    # Default candidates if none provided
    if candidate_names is None:
        candidate_names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve']
    
    # Seed initial data
    for name in candidate_names:
        cursor.execute(
            'INSERT OR IGNORE INTO votes (name, votes) VALUES (?, ?)',
            (name, 0)
        )
        print(f"Added candidate: {name}")
    
    conn.commit()
    conn.close()
    print(f"\nDatabase initialized successfully at: {os.path.abspath(DATABASE)}")
    print(f"Total candidates: {len(candidate_names)}")
    return candidate_names

def reset_votes():
    """Reset all vote counts to zero without removing candidates."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE votes SET votes = 0')
    conn.commit()
    conn.close()
    print("All vote counts reset to 0")

def get_all_votes():
    """Fetch all names and their vote counts."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT name, votes FROM votes ORDER BY name')
    results = [{'name': row['name'], 'votes': row['votes']} for row in cursor.fetchall()]
    conn.close()
    return results

def add_candidate(name):
    """Add a new candidate to the database."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO votes (name, votes) VALUES (?, ?)', (name, 0))
        conn.commit()
        print(f"Added new candidate: {name}")
        return True
    except sqlite3.IntegrityError:
        print(f"Candidate '{name}' already exists")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    # When run directly, initialize with defaults
    import sys
    if len(sys.argv) > 1:
        # Accept names as command line arguments
        names = sys.argv[1:]
        init_db(names)
    else:
        init_db()