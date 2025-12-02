#!/usr/bin/env python3
"""
Fix all SQL placeholder issues for PostgreSQL compatibility
"""

import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    i = 0
    changes_made = 0

    while i < len(lines):
        line = lines[i]
        original_line = line

        # Skip if already has db.convert_sql
        if 'db.convert_sql' in line:
            fixed_lines.append(line)
            i += 1
            continue

        # Fix cursor.execute with "..." containing ?
        if 'cursor.execute(' in line and '?' in line and '"' in line:
            # Match: cursor.execute("...", ...)
            match = re.match(r'(\s*)(.*)cursor\.execute\("([^"]*\?[^"]*)"(.*)$', line)
            if match:
                indent, before, sql, after = match.groups()
                line = f'{indent}{before}cursor.execute(db.convert_sql("{sql}"){after}\n'
                changes_made += 1

        # Fix cursor.execute with """...""" containing ?
        elif 'cursor.execute("""' in line and '?' in line:
            line = line.replace('cursor.execute("""', 'cursor.execute(db.convert_sql("""')
            # Need to find the closing """ and add )
            j = i
            while j < len(lines) and '"""' not in lines[j][lines[j].index('"""')+3:]:
                j += 1
            if j < len(lines):
                lines[j] = lines[j].replace('""",', """),""", 1)
                lines[j] = lines[j].replace('""")', """))", 1)
            changes_made += 1

        # Fix pd.read_sql_query with "..." containing ?
        elif 'pd.read_sql_query(' in line and '?' in line and '"' in line and 'db.convert_sql' not in line:
            # Match: pd.read_sql_query("...", ...)
            match = re.match(r'(\s*)(.*)pd\.read_sql_query\("([^"]*\?[^"]*)"(.*)$', line)
            if match:
                indent, before, sql, after = match.groups()
                line = f'{indent}{before}pd.read_sql_query(db.convert_sql("{sql}"){after}\n'
                changes_made += 1

        # Fix pd.read_sql_query with """...""" containing ?
        elif 'pd.read_sql_query("""' in line and '?' in line:
            line = line.replace('pd.read_sql_query("""', 'pd.read_sql_query(db.convert_sql("""')
            # Find closing """ and add )
            j = i
            found_close = False
            while j < len(lines) and not found_close:
                if '"""' in lines[j] and (j > i or lines[j].count('"""') > 1):
                    # Found closing
                    lines[j] = lines[j].replace('"""', """)""", 1)
                    found_close = True
                j += 1
            changes_made += 1

        fixed_lines.append(line)
        i += 1

    if changes_made > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        print(f"✅ Made {changes_made} fixes to {filepath}")
        return True
    else:
        print(f"ℹ️  No changes needed in {filepath}")
        return False

if __name__ == "__main__":
    fixed = fix_file("app_multiuser.py")
    if fixed:
        print("\n✅ All SQL placeholders have been fixed!")
        print("📝 The file has been updated - please review it")
    else:
        print("\n✅ File is already up to date")
