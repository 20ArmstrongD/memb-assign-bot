import sqlite3
from datetime import datetime

# Path to the SQLite database
DATABASE_PATH = '/home/DiscordPi/code/discord_bots/memb-assign-bot/logs.db'

def connect_db():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    return conn

def log_request(username, action, approval_status, approver=None):
    """Log the request details to the SQLite database."""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Create the requests table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            approval_status TEXT NOT NULL,
            approver TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Convert approval_status to 'yes' or 'no'
    approval_status_str = 'yes' if approval_status else 'no'
    
    # Insert the new request into the database
    cursor.execute('''
        INSERT INTO requests (username, action, approval_status, approver, timestamp)
        VALUES (?, ?, ?, ?, datetime('now'))
    ''', (username, action, approval_status_str, approver))
    
    conn.commit()
    conn.close()