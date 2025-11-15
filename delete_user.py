"""
Script to delete users from the productivity planner database
WARNING: This will also delete all associated tasks, goals, entries, and achievements!
"""
import sqlite3
import pandas as pd
import os

db_path = "productivity_planner_multiuser.db"

if not os.path.exists(db_path):
    print("Database doesn't exist yet!")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Show all users
print("=== REGISTERED USERS ===\n")
users = pd.read_sql_query("""
    SELECT id, username, email, created_at
    FROM users
    ORDER BY id
""", conn)

if users.empty:
    print("No users found!")
    conn.close()
    exit()

print(users.to_string(index=False))
print("\n")

# Get user input
username_to_delete = input("Enter the USERNAME to delete (or 'cancel' to exit): ").strip()

if username_to_delete.lower() == 'cancel':
    print("Cancelled.")
    conn.close()
    exit()

# Check if user exists
user_check = pd.read_sql_query("""
    SELECT id, username FROM users WHERE username = ?
""", conn, params=(username_to_delete,))

if user_check.empty:
    print(f"User '{username_to_delete}' not found!")
    conn.close()
    exit()

user_id = user_check.iloc[0]['id']

# Get counts of data to be deleted
tasks_count = pd.read_sql_query(
    "SELECT COUNT(*) as count FROM tasks WHERE user_id = ?",
    conn, params=(user_id,)
).iloc[0]['count']

goals_count = pd.read_sql_query(
    "SELECT COUNT(*) as count FROM goals WHERE user_id = ?",
    conn, params=(user_id,)
).iloc[0]['count']

entries_count = pd.read_sql_query(
    "SELECT COUNT(*) as count FROM daily_entries WHERE user_id = ?",
    conn, params=(user_id,)
).iloc[0]['count']

achievements_count = pd.read_sql_query(
    "SELECT COUNT(*) as count FROM achievements WHERE user_id = ?",
    conn, params=(user_id,)
).iloc[0]['count']

# Show what will be deleted
print(f"\n⚠️  WARNING: Deleting user '{username_to_delete}' will also delete:")
print(f"   - {tasks_count} tasks")
print(f"   - {goals_count} goals")
print(f"   - {entries_count} daily journal entries")
print(f"   - {achievements_count} achievements")
print("\nThis action CANNOT be undone!\n")

# Confirm deletion
confirm = input("Type 'DELETE' to confirm: ").strip()

if confirm != 'DELETE':
    print("Deletion cancelled.")
    conn.close()
    exit()

# Delete all related data
try:
    cursor.execute("DELETE FROM achievements WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM daily_entries WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

    conn.commit()
    print(f"\n✅ User '{username_to_delete}' and all associated data have been deleted successfully!")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error deleting user: {e}")

conn.close()
