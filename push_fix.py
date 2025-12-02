#!/usr/bin/env python3
"""Script to check git status and push changes"""
import subprocess
import os

os.chdir(r"c:\Users\jmikn\OneDrive\Documents\Side Projects\Python_Side_Projects\productivity_planner")

print("=== Git Status ===")
result = subprocess.run(["git", "status"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)

print("\n=== File Size ===")
import os
size = os.path.getsize("app_multiuser.py")
print(f"app_multiuser.py: {size} bytes")

print("\n=== Line Count ===")
with open("app_multiuser.py", "r", encoding="utf-8") as f:
    lines = len(f.readlines())
print(f"app_multiuser.py: {lines} lines")

print("\n=== Git Diff (first 20 lines) ===")
result = subprocess.run(["git", "diff", "HEAD", "--", "app_multiuser.py"], capture_output=True, text=True)
diff_lines = result.stdout.split('\n')[:20]
for line in diff_lines:
    print(line)

print("\n=== Attempting to add and commit ===")
result = subprocess.run(["git", "add", "-v", "app_multiuser.py"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)

result = subprocess.run(["git", "commit", "-m", "PostgreSQL migration fixes"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)

result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)
