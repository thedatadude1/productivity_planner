#!/usr/bin/env python3
"""Fix the syntax error on line 970"""
import re

with open("app_multiuser.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find and fix the problematic pattern
old_pattern = r'weekly_tasks = pd\.read_sql_query\(db\.convert_sql\("""[\s\S]*?WHERE user_id = \? AND status = \'completed\' AND completed_at >= \?[\s\S]*?ORDER BY date[\s\S]*?"""\), conn, params=\[user_id, week_ago\.strftime\("%Y-%m-%d"\)\]\)'

new_code = '''week_ago_str = week_ago.strftime("%Y-%m-%d")
        weekly_query = db.convert_sql("""
            SELECT DATE(completed_at) as date, COUNT(*) as count
            FROM tasks
            WHERE user_id = ? AND status = 'completed' AND completed_at >= ?
            GROUP BY DATE(completed_at)
            ORDER BY date
        """)
        weekly_tasks = pd.read_sql_query(weekly_query, conn, params=[user_id, week_ago_str])'''

# Try to find the line with week_ago.strftime
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'week_ago.strftime' in line:
        print(f"Line {i+1}: {repr(line)}")

# Find the block from "week_ago = datetime" to the closing of read_sql_query
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if 'week_ago = datetime.now()' in line and 'timedelta(days=7)' in line:
        start_idx = i
    if start_idx is not None and 'week_ago.strftime' in line:
        end_idx = i
        break

if start_idx is not None and end_idx is not None:
    print(f"\nFound block from line {start_idx+1} to {end_idx+1}")
    print("Current block:")
    for i in range(start_idx, end_idx+1):
        print(f"  {i+1}: {repr(lines[i])}")

    # Replace the block
    new_lines = lines[:start_idx]
    new_lines.append('        week_ago = datetime.now() - timedelta(days=7)')
    new_lines.append('        week_ago_str = week_ago.strftime("%Y-%m-%d")')
    new_lines.append('        weekly_query = db.convert_sql("""')
    new_lines.append('            SELECT DATE(completed_at) as date, COUNT(*) as count')
    new_lines.append('            FROM tasks')
    new_lines.append("            WHERE user_id = ? AND status = 'completed' AND completed_at >= ?")
    new_lines.append('            GROUP BY DATE(completed_at)')
    new_lines.append('            ORDER BY date')
    new_lines.append('        """)')
    new_lines.append('        weekly_tasks = pd.read_sql_query(weekly_query, conn, params=[user_id, week_ago_str])')
    new_lines.extend(lines[end_idx+1:])

    with open("app_multiuser.py", "w", encoding="utf-8") as f:
        f.write('\n'.join(new_lines))

    print("\nFile updated successfully!")
else:
    print("Could not find the block to replace")
