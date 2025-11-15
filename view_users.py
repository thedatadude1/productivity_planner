"""
Simple script to view registered users (usernames only, not passwords)
Passwords are securely hashed and cannot be retrieved
"""
import sqlite3
import pandas as pd
import os

db_path = "productivity_planner_multiuser.db"

if not os.path.exists(db_path):
    print("Database doesn't exist yet. Run the app first to create it!")
else:
    conn = sqlite3.connect(db_path)

    print("=== REGISTERED USERS ===\n")

    # Get users (without password hashes for security)
    users = pd.read_sql_query("""
        SELECT id, username, email, created_at
        FROM users
        ORDER BY created_at DESC
    """, conn)

    if users.empty:
        print("No users registered yet!")
    else:
        print(users.to_string(index=False))
        print(f"\nTotal users: {len(users)}")

    print("\n=== PASSWORD SECURITY ===")
    print("Passwords are hashed using Argon2 and CANNOT be viewed.")
    print("Example of what a hashed password looks like:\n")

    # Show example of password hash (if any users exist)
    if not users.empty:
        sample_hash = pd.read_sql_query("""
            SELECT password_hash FROM users LIMIT 1
        """, conn)
        print(sample_hash.iloc[0]['password_hash'])
        print("\n^ This cannot be reversed to get the original password!")

    conn.close()
