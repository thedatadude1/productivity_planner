#!/usr/bin/env python3
"""Push the corrected app_multiuser.py to GitHub"""
import subprocess
import os

os.chdir(r"c:\Users\jmikn\OneDrive\Documents\Side Projects\Python_Side_Projects\productivity_planner")

print("=== Checking git status ===")
result = subprocess.run(["git", "status"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)

print("\n=== Adding app_multiuser.py ===")
result = subprocess.run(["git", "add", "app_multiuser.py"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)

print("\n=== Git diff --stat ===")
result = subprocess.run(["git", "diff", "--cached", "--stat"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)

print("\n=== Committing ===")
result = subprocess.run(["git", "commit", "-m", "PostgreSQL migration - all syntax errors fixed (2497 lines)"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)

print("\n=== Pushing to origin main ===")
result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)

print("\n=== Final status ===")
result = subprocess.run(["git", "status"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)

print("\n=== DONE ===")
