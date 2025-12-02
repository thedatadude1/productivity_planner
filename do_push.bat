@echo off
cd /d "c:\Users\jmikn\OneDrive\Documents\Side Projects\Python_Side_Projects\productivity_planner"

echo === Current git status ===
git status

echo.
echo === Removing app_multiuser.py from git cache ===
git rm --cached app_multiuser.py

echo.
echo === Adding file back ===
git add app_multiuser.py

echo.
echo === Git status after re-add ===
git status

echo.
echo === Committing ===
git commit -m "PostgreSQL migration - fixed all syntax errors"

echo.
echo === Pushing ===
git push origin main

echo.
echo === Done! Check GitHub ===
pause
