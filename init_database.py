"""
Initialize the database with all required tables
Run this before using view_users.py or delete_user.py
"""
import sqlite3

db_path = "productivity_planner_multiuser.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Initializing database tables...\n")

# Users table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        is_admin INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Tasks table with user_id
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        priority TEXT,
        status TEXT DEFAULT 'pending',
        due_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        estimated_hours REAL,
        tags TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

# Goals table with user_id
cursor.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        target_date DATE,
        progress INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

# Daily entries table with user_id
cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        entry_date DATE,
        mood INTEGER,
        gratitude TEXT,
        highlights TEXT,
        challenges TEXT,
        tomorrow_goals TEXT,
        UNIQUE(user_id, entry_date),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

# Achievements table with user_id
cursor.execute("""
    CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        icon TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

conn.commit()

# Verify tables were created
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("✅ Database initialized successfully!\n")
print("Tables created:")
for table in tables:
    print(f"  - {table[0]}")

conn.close()

print("\nYou can now run:")
print("  - python view_users.py")
print("  - python delete_user.py")
print("  - python -m streamlit run app_multiuser.py")
