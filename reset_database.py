"""
Script to completely reset the database (delete all users and data)
USE WITH CAUTION!
"""
import os

db_path = "productivity_planner_multiuser.db"

if not os.path.exists(db_path):
    print("Database doesn't exist yet!")
    exit()

print("⚠️  WARNING: This will DELETE the entire database!")
print("All users, tasks, goals, journal entries, and achievements will be PERMANENTLY DELETED!")
print("\nThis action CANNOT be undone!\n")

confirm = input("Type 'RESET' to confirm: ").strip()

if confirm != 'RESET':
    print("Reset cancelled.")
    exit()

try:
    os.remove(db_path)
    print("\n✅ Database has been completely reset!")
    print("The database will be recreated when you run the app again.")
except Exception as e:
    print(f"\n❌ Error resetting database: {e}")
