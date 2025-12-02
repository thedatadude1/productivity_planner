#!/usr/bin/env python3
"""Force push the app_multiuser.py file to GitHub by recreating it"""
import subprocess
import os
import shutil

os.chdir(r"c:\Users\jmikn\OneDrive\Documents\Side Projects\Python_Side_Projects\productivity_planner")

print("Step 1: Reading current app_multiuser.py content...")
with open("app_multiuser.py", "r", encoding="utf-8") as f:
    content = f.read()

print(f"  - File has {len(content)} characters and {content.count(chr(10))+1} lines")

print("\nStep 2: Backing up to app_backup.py...")
shutil.copy("app_multiuser.py", "app_backup.py")

print("\nStep 3: Deleting app_multiuser.py...")
os.remove("app_multiuser.py")

print("\nStep 4: Running git rm to remove from tracking...")
result = subprocess.run(["git", "rm", "-f", "app_multiuser.py"], capture_output=True, text=True)
print(f"  stdout: {result.stdout}")
print(f"  stderr: {result.stderr}")

print("\nStep 5: Recreating app_multiuser.py from backup...")
shutil.copy("app_backup.py", "app_multiuser.py")

print("\nStep 6: Adding new file to git...")
result = subprocess.run(["git", "add", "app_multiuser.py"], capture_output=True, text=True)
print(f"  stdout: {result.stdout}")
print(f"  stderr: {result.stderr}")

print("\nStep 7: Checking git status...")
result = subprocess.run(["git", "status"], capture_output=True, text=True)
print(result.stdout)

print("\nStep 8: Committing...")
result = subprocess.run(["git", "commit", "-m", "Force update app_multiuser.py - PostgreSQL migration complete"], capture_output=True, text=True)
print(f"  stdout: {result.stdout}")
print(f"  stderr: {result.stderr}")

print("\nStep 9: Pushing to GitHub...")
result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
print(f"  stdout: {result.stdout}")
print(f"  stderr: {result.stderr}")

print("\nStep 10: Cleaning up backup...")
if os.path.exists("app_backup.py"):
    os.remove("app_backup.py")

print("\n=== DONE ===")
print("Check https://github.com/thedatadude1/productivity_planner to verify the push worked!")
