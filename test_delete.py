"""
Test deletion script to verify user deletion works
"""
import sqlite3

db_path = "productivity_planner_multiuser.db"

# Show current users
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== CURRENT USERS ===")
cursor.execute("SELECT id, username FROM users")
users = cursor.fetchall()
for user in users:
    print(f"ID: {user[0]}, Username: {user[1]}")

conn.close()

print("\n=== ATTEMPTING TO DELETE thedatadude3 ===")

# Get the user ID
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id FROM users WHERE username = ?", ("thedatadude3",))
result = cursor.fetchone()

if result:
    user_id = result[0]
    print(f"Found user with ID: {user_id}")

    try:
        # Disable foreign keys
        cursor.execute("PRAGMA foreign_keys = OFF")

        # Delete all related data
        cursor.execute("DELETE FROM achievements WHERE user_id = ?", (user_id,))
        print(f"Deleted achievements: {cursor.rowcount}")

        cursor.execute("DELETE FROM daily_entries WHERE user_id = ?", (user_id,))
        print(f"Deleted daily entries: {cursor.rowcount}")

        cursor.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))
        print(f"Deleted goals: {cursor.rowcount}")

        cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        print(f"Deleted tasks: {cursor.rowcount}")

        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        print(f"Deleted user: {cursor.rowcount}")

        conn.commit()
        print("\n✅ Deletion successful!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
else:
    print("User 'thedatadude3' not found!")

conn.close()

print("\n=== USERS AFTER DELETION ===")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT id, username FROM users")
users = cursor.fetchall()
for user in users:
    print(f"ID: {user[0]}, Username: {user[1]}")
conn.close()
