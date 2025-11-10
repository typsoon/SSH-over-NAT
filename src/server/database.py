# database.py
import sqlite3
import bcrypt

DATABASE_NAME = 'users.db'

def setup_database():
    """Initializes the database and creates the users table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully.")

def add_user(username, password):
    """Adds a new user to the database with a hashed password."""
    try:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # This error occurs if the username already exists
        return False

def authenticate_user(username, password):
    """Authenticates a user against the stored hashed password."""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result:
        stored_hash = result[0]
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
    return False