import sqlite3
from argon2 import PasswordHasher

ph = PasswordHasher()
db_path = "productivity_planner_multiuser.db"

ADMIN_USERNAME = "thedatadude"
ADMIN_PASSWORD = "Jacobm1313!"
ADMIN_EMAIL = "admin@productivity.app"

print("Setting up admin account...")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    print("Added is_admin column")
except:
    print("is_admin column exists")

cursor.execute("UPDATE users SET is_admin = 0")
print("Removed admin from all users")

cursor.execute("SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,))
existing = cursor.fetchone()

password_hash = ph.hash(ADMIN_PASSWORD)

if existing:
    cursor.execute("UPDATE users SET password_hash = ?, email = ?, is_admin = 1 WHERE id = ?",
                  (password_hash, ADMIN_EMAIL, existing[0]))
    print(f"Updated {ADMIN_USERNAME} as admin")
else:
    cursor.execute("INSERT INTO users (username, password_hash, email, is_admin) VALUES (?, ?, ?, 1)",
                  (ADMIN_USERNAME, password_hash, ADMIN_EMAIL))
    print(f"Created {ADMIN_USERNAME} as admin")

conn.commit()
conn.close()

print(f"\nAdmin account ready: {ADMIN_USERNAME}")
print("This is the ONLY admin account")
