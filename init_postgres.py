"""
Initialize PostgreSQL database with all required tables
Run this once after adding DATABASE_URL to Streamlit secrets
"""

import psycopg2
from argon2 import PasswordHasher

DATABASE_URL = "postgresql://neondb_owner:npg_0xqhVGEgnm3O@ep-icy-dust-af18qqjt-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def init_postgres_database():
    """Initialize all tables in PostgreSQL"""
    print("🚀 Initializing PostgreSQL database...")
    print("-" * 60)

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        print("✅ Connected to PostgreSQL")

        # Users table
        print("📝 Creating users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                is_admin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tasks table
        print("📝 Creating tasks table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                priority TEXT,
                status TEXT DEFAULT 'pending',
                due_date TEXT,
                estimated_hours REAL,
                actual_hours REAL,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Goals table
        print("📝 Creating goals table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                target_date TEXT,
                progress INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Daily entries table
        print("📝 Creating daily_entries table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_entries (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                mood TEXT,
                energy_level INTEGER,
                productivity_rating INTEGER,
                notes TEXT,
                highlights TEXT,
                challenges TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, date)
            )
        """)

        # Achievements table
        print("📝 Creating achievements table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                achievement_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        conn.commit()
        print("✅ All tables created successfully")

        # Create admin user
        print("👤 Creating admin user...")
        ph = PasswordHasher()
        username = "thedatadude"
        password = "Jacobm1313!"
        password_hash = ph.hash(password)

        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, is_admin)
                VALUES (%s, %s, %s, %s)
            """, (username, password_hash, None, 1))
            conn.commit()
            print(f"✅ Admin user created: {username}")
        except psycopg2.IntegrityError:
            conn.rollback()
            print(f"ℹ️  Admin user '{username}' already exists")

        # Verify setup
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"\n📊 Database status:")
        print(f"   - Users: {user_count}")

        cursor.close()
        conn.close()

        print("-" * 60)
        print("🎉 PostgreSQL database is ready!")
        print(f"\n🔐 Login credentials:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print("\n✅ You can now deploy your app to Streamlit Cloud!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_postgres_database()
