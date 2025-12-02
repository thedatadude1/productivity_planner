"""
Automatically fix SQL parameter placeholders in app_multiuser.py
Wraps all SQL queries with db.convert_sql() for PostgreSQL compatibility
"""

import re

FILE_PATH = "app_multiuser.py"

def fix_sql_placeholders():
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Fix pd.read_sql_query with direct string (not already using db.convert_sql)
    # Pattern: pd.read_sql_query("...", conn, ...)
    # But skip if already wrapped with db.convert_sql
    pattern1 = r'pd\.read_sql_query\("""((?:(?!""").)+)"""'
    def replace_read_sql_multiline(match):
        sql = match.group(1)
        if '?' in sql:
            return f'pd.read_sql_query(db.convert_sql("""{sql}"""'
        return match.group(0)

    content = re.sub(pattern1, replace_read_sql_multiline, content, flags=re.DOTALL)

    # Fix pd.read_sql_query with single quotes
    pattern2 = r'pd\.read_sql_query\("([^"]+)"'
    def replace_read_sql_single(match):
        sql = match.group(1)
        if '?' in sql and 'db.convert_sql' not in sql:
            return f'pd.read_sql_query(db.convert_sql("{sql}")'
        return match.group(0)

    content = re.sub(pattern2, replace_read_sql_single, content)

    # Fix cursor.execute with ? placeholders
    pattern3 = r'cursor\.execute\("([^"]+\?[^"]*)"'
    def replace_cursor_execute(match):
        sql = match.group(1)
        if 'db.convert_sql' not in sql:
            return f'cursor.execute(db.convert_sql("{sql}")'
        return match.group(0)

    content = re.sub(pattern3, replace_cursor_execute, content)

    # Fix cursor.execute with triple quotes
    pattern4 = r'cursor\.execute\("""((?:(?!""").)+)"""'
    def replace_cursor_execute_multiline(match):
        sql = match.group(1)
        if '?' in sql:
            return f'cursor.execute(db.convert_sql("""{sql}"""'
        return match.group(0)

    content = re.sub(pattern4, replace_cursor_execute_multiline, content, flags=re.DOTALL)

    if content != original_content:
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Fixed SQL placeholders in app_multiuser.py")
        print("📝 Changes applied - please review the file")
    else:
        print("ℹ️  No changes needed")

if __name__ == "__main__":
    fix_sql_placeholders()
