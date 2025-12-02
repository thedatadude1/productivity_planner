"""
Test PostgreSQL connection to Neon database
Run this locally to verify the connection works before deploying
"""

import psycopg2
from psycopg2 import OperationalError

DATABASE_URL = "postgresql://neondb_owner:npg_0xqhVGEgnm3O@ep-icy-dust-af18qqjt-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def test_connection():
    """Test basic connection to PostgreSQL"""
    print("🔍 Testing PostgreSQL connection to Neon...")
    print("-" * 60)

    try:
        # Attempt connection
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Connection successful!")

        # Test basic query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL version: {version[0][:50]}...")

        # Check existing tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()

        if tables:
            print(f"✅ Found {len(tables)} existing table(s):")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("ℹ️  No tables found (will be created on first app run)")

        cursor.close()
        conn.close()

        print("-" * 60)
        print("🎉 PostgreSQL is ready! You can now add DATABASE_URL to Streamlit secrets.")
        return True

    except OperationalError as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check that the connection string is correct")
        print("2. Verify your Neon database is active (not paused)")
        print("3. Check firewall/network settings")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
