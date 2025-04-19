import sqlite3
import bcrypt

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            password TEXT,
            nickname TEXT
        )
    """)
    conn.commit()
    conn.close()

def register_user(user_id, password, nickname):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if cur.fetchone():
        raise ValueError("사용 중인 아이디입니다.")
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    cur.execute("INSERT INTO users (user_id, password, nickname) VALUES (?, ?, ?)",
                (user_id, hashed_pw, nickname))
    conn.commit()
    conn.close()

def login_user(user_id, password):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row and bcrypt.checkpw(password.encode(), row[0])

def get_user_nickname(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT nickname FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
