import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Optional
import random
import json
import hashlib
import os
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# PostgreSQL imports (required)
import psycopg2

# Google Gemini AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Ultimate Productivity Planner",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1rem 0;
    }
    .motivational-quote {
        font-size: 1.2rem;
        font-style: italic;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border-radius: 10px;
        margin: 1rem 0;
    }
    .achievement-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0.5rem;
        border-radius: 20px;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# Database initialization
class DatabaseManager:
    def __init__(self, db_name="productivity_planner_multiuser.db"):
        # PostgreSQL only - DATABASE_URL must be set in Streamlit secrets
        try:
            if hasattr(st, 'secrets') and "DATABASE_URL" in st.secrets:
                self.database_url = st.secrets["DATABASE_URL"]
            else:
                raise ValueError("DATABASE_URL not found in Streamlit secrets. Please add your Neon PostgreSQL connection string.")
        except Exception as e:
            st.error(f"⚠️ Database configuration error: {str(e)}")
            st.info("Please add DATABASE_URL to your Streamlit secrets with your Neon PostgreSQL connection string.")
            st.stop()

        self.init_database()

    def get_connection(self):
        # Always use PostgreSQL
        return psycopg2.connect(self.database_url)

    def convert_sql(self, query):
        """Convert SQL query placeholders from SQLite (?) to PostgreSQL (%s)"""
        return query.replace('?', '%s')

    def init_database(self):
        """Initialize PostgreSQL database with all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
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

        # Tasks table with user_id
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                priority TEXT,
                status TEXT DEFAULT 'pending',
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                estimated_hours REAL,
                tags TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Goals table with user_id
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                target_date DATE,
                progress INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Daily entries table with user_id
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_entries (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                entry_date DATE,
                mood INTEGER,
                gratitude TEXT,
                highlights TEXT,
                challenges TEXT,
                tomorrow_goals TEXT,
                UNIQUE(user_id, entry_date),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Achievements table with user_id
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                icon TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Ensure admin account exists (for first-time setup)
        cursor.execute("SELECT id FROM users WHERE username = 'thedatadude'")
        admin_exists = cursor.fetchone()

        if not admin_exists:
            # Create admin account with Argon2 hash
            from argon2 import PasswordHasher
            ph_init = PasswordHasher()
            admin_hash = ph_init.hash("Jacobm1313!")

            cursor.execute("""
                INSERT INTO users (username, password_hash, email, is_admin)
                VALUES ('thedatadude', %s, 'admin@productivity.app', 1)
            """, (admin_hash,))

        conn.commit()
        conn.close()

# Initialize database
db = DatabaseManager()

# Initialize Argon2 password hasher
ph = PasswordHasher()

# Fireworks Effect Function
def show_fireworks():
    """Display a fireworks celebration effect"""
    # Use a combination of emojis and success message for celebration
    st.markdown("""
    <style>
    @keyframes firework-burst {
        0% { transform: scale(0) rotate(0deg); opacity: 1; }
        50% { transform: scale(1.2) rotate(180deg); opacity: 0.8; }
        100% { transform: scale(2) rotate(360deg); opacity: 0; }
    }
    .fireworks-celebration {
        font-size: 3rem;
        text-align: center;
        animation: firework-burst 1.5s ease-out;
        margin: 20px 0;
    }
    </style>
    <div class="fireworks-celebration">
    🎆 🎇 ✨ 🎉 🎊 ✨ 🎇 🎆
    </div>
    """, unsafe_allow_html=True)

    # Also use balloons as a reliable fallback
    st.balloons()

# Authentication Functions
def register_user(username, password, email=""):
    """Register a new user with Argon2 password hashing"""
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        # Hash password using Argon2
        password_hash = ph.hash(password)
        cursor.execute(db.convert_sql("""
            INSERT INTO users (username, password_hash, email)
            VALUES (?, ?, ?)
        """), (username, password_hash, email))
        conn.commit()
        conn.close()
        return True
    except Exception:
        # Handle unique constraint violation (username already exists)
        conn.close()
        return False

def login_user(username, password):
    """Login user with password verification (supports both Argon2 and legacy SHA-256)"""
    conn = db.get_connection()
    cursor = conn.cursor()

    # Get user by username
    user = pd.read_sql_query(db.convert_sql("""
        SELECT id, username, password_hash, is_admin FROM users
        WHERE username = ?
    """), conn, params=(username,))

    if not user.empty:
        user_id = user.iloc[0]['id']
        stored_hash = user.iloc[0]['password_hash']
        is_admin = bool(user.iloc[0]['is_admin'])

        # Try Argon2 verification first (new format)
        try:
            ph.verify(stored_hash, password)
            conn.close()
            return user_id, username, is_admin
        except VerifyMismatchError:
            # If Argon2 fails, try SHA-256 (legacy format)
            sha256_hash = hashlib.sha256(password.encode()).hexdigest()
            if stored_hash == sha256_hash:
                # Password is correct but using old hash format
                # Upgrade to Argon2 automatically
                new_hash = ph.hash(password)
                cursor.execute(db.convert_sql("UPDATE users SET password_hash = ? WHERE id = ?"),
                             (new_hash, user_id))
                conn.commit()
                conn.close()
                return user_id, username, is_admin
            else:
                # Wrong password with both methods
                conn.close()
                return None, None, False
        except Exception:
            # If Argon2 verification throws any other error, try SHA-256
            sha256_hash = hashlib.sha256(password.encode()).hexdigest()
            if stored_hash == sha256_hash:
                # Password is correct but using old hash format
                # Upgrade to Argon2 automatically
                new_hash = ph.hash(password)
                cursor.execute(db.convert_sql("UPDATE users SET password_hash = ? WHERE id = ?"),
                             (new_hash, user_id))
                conn.commit()
                conn.close()
                return user_id, username, is_admin
            else:
                conn.close()
                return None, None, False

    conn.close()
    return None, None, False

# Motivational quotes
MOTIVATIONAL_QUOTES = [
    "The secret of getting ahead is getting started. - Mark Twain",
    "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
    "The only way to do great work is to love what you do. - Steve Jobs",
    "Don't watch the clock; do what it does. Keep going. - Sam Levenson",
    "The future depends on what you do today. - Mahatma Gandhi",
    "Believe you can and you're halfway there. - Theodore Roosevelt",
    "You are never too old to set another goal or to dream a new dream. - C.S. Lewis",
    "The harder you work for something, the greater you'll feel when you achieve it.",
    "Dream bigger. Do bigger.",
    "Push yourself, because no one else is going to do it for you.",
]

def get_daily_quote():
    random.seed(datetime.now().strftime("%Y-%m-%d"))
    return random.choice(MOTIVATIONAL_QUOTES)

# Task Management Functions (now user-specific)
def add_task(user_id, title, description, category, priority, due_date, estimated_hours, tags):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(db.convert_sql("""
        INSERT INTO tasks (user_id, title, description, category, priority, due_date, estimated_hours, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """), (user_id, title, description, category, priority, due_date, estimated_hours, json.dumps(tags)))
    conn.commit()
    conn.close()
    check_achievements(user_id)

def get_tasks(user_id, status=None, category=None):
    conn = db.get_connection()
    query = "SELECT * FROM tasks WHERE user_id = ?"
    params = [user_id]

    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY due_date ASC, priority DESC"

    df = pd.read_sql_query(db.convert_sql(query), conn, params=params)
    conn.close()
    return df

def update_task_status(user_id, task_id, new_status):
    conn = db.get_connection()
    cursor = conn.cursor()

    if new_status == 'completed':
        cursor.execute(db.convert_sql("""
            UPDATE tasks SET status = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """), (new_status, task_id, user_id))
    else:
        cursor.execute(db.convert_sql("""
            UPDATE tasks SET status = ?
            WHERE id = ? AND user_id = ?
        """), (new_status, task_id, user_id))

    conn.commit()
    conn.close()
    check_achievements(user_id)

def delete_task(user_id, task_id):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(db.convert_sql("DELETE FROM tasks WHERE id = ? AND user_id = ?"), (task_id, user_id))
    conn.commit()
    conn.close()

# Goal Management Functions (now user-specific)
def add_goal(user_id, title, description, target_date):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(db.convert_sql("""
        INSERT INTO goals (user_id, title, description, target_date)
        VALUES (?, ?, ?, ?)
    """), (user_id, title, description, target_date))
    conn.commit()
    conn.close()

def get_goals(user_id, status='active'):
    conn = db.get_connection()
    df = pd.read_sql_query(
        db.convert_sql("SELECT * FROM goals WHERE user_id = ? AND status = ? ORDER BY target_date ASC"),
        conn,
        params=(user_id, status)
    )
    conn.close()
    return df

def update_goal_progress(user_id, goal_id, progress):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(db.convert_sql("""
        UPDATE goals SET progress = ?, status = ?
        WHERE id = ? AND user_id = ?
    """), (progress, 'completed' if progress >= 100 else 'active', goal_id, user_id))
    conn.commit()
    conn.close()
    check_achievements(user_id)

# Analytics Functions (now user-specific)
def get_productivity_stats(user_id):
    conn = db.get_connection()

    total_tasks = pd.read_sql_query(
        db.convert_sql("SELECT COUNT(*) as count FROM tasks WHERE user_id = ?"),
        conn, params=(user_id,)
    ).iloc[0]['count']

    completed_tasks = pd.read_sql_query(
        db.convert_sql("SELECT COUNT(*) as count FROM tasks WHERE user_id = ? AND status = 'completed'"),
        conn, params=(user_id,)
    ).iloc[0]['count']

    week_completed = pd.read_sql_query(db.convert_sql("""
        SELECT COUNT(*) as count FROM tasks
        WHERE user_id = ? AND status = 'completed'
        AND completed_at >= date('now', '-7 days')
    """), conn, params=(user_id,)).iloc[0]['count']

    streak = calculate_streak(user_id)

    active_goals = pd.read_sql_query(
        db.convert_sql("SELECT COUNT(*) as count FROM goals WHERE user_id = ? AND status = 'active'"),
        conn, params=(user_id,)
    ).iloc[0]['count']

    conn.close()

    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'week_completed': week_completed,
        'streak': streak,
        'active_goals': active_goals,
        'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    }

def calculate_streak(user_id):
    conn = db.get_connection()
    df = pd.read_sql_query(db.convert_sql("""
        SELECT DATE(completed_at) as date FROM tasks
        WHERE user_id = ? AND status = 'completed'
        ORDER BY completed_at DESC
    """), conn, params=(user_id,))
    conn.close()

    if df.empty:
        return 0

    streak = 0
    current_date = datetime.now().date()

    for date_str in df['date'].unique():
        task_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if task_date == current_date:
            streak += 1
            current_date -= timedelta(days=1)
        elif task_date == current_date - timedelta(days=1):
            streak += 1
            current_date = task_date - timedelta(days=1)
        else:
            break

    return streak

# Achievement System (now user-specific)
def check_achievements(user_id):
    conn = db.get_connection()
    cursor = conn.cursor()

    stats = get_productivity_stats(user_id)

    achievements = [
        (5, "First Steps", "Completed 5 tasks", "🌱"),
        (25, "Getting Started", "Completed 25 tasks", "🚀"),
        (50, "Halfway Hero", "Completed 50 tasks", "⭐"),
        (100, "Century Club", "Completed 100 tasks", "💯"),
        (7, "Week Warrior", "7-day streak", "🔥"),
        (30, "Monthly Master", "30-day streak", "👑"),
    ]

    for threshold, name, description, icon in achievements:
        existing = pd.read_sql_query(
            db.convert_sql("SELECT * FROM achievements WHERE user_id = ? AND name = ?"),
            conn,
            params=(user_id, name)
        )

        if existing.empty:
            if threshold <= 50 and stats['completed_tasks'] >= threshold:
                cursor.execute(db.convert_sql("""
                    INSERT INTO achievements (user_id, name, description, icon)
                    VALUES (?, ?, ?, ?)
                """), (user_id, name, description, icon))
            elif threshold > 50 and stats['streak'] >= threshold:
                cursor.execute(db.convert_sql("""
                    INSERT INTO achievements (user_id, name, description, icon)
                    VALUES (?, ?, ?, ?)
                """), (user_id, name, description, icon))

    conn.commit()
    conn.close()

def get_achievements(user_id):
    conn = db.get_connection()
    df = pd.read_sql_query(
        db.convert_sql("SELECT * FROM achievements WHERE user_id = ? ORDER BY earned_at DESC"),
        conn, params=(user_id,)
    )
    conn.close()
    return df

# Daily Entry Functions (now user-specific)
def save_daily_entry(user_id, entry_date, mood, gratitude, highlights, challenges, tomorrow_goals):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(db.convert_sql("""
        INSERT OR REPLACE INTO daily_entries
        (user_id, entry_date, mood, gratitude, highlights, challenges, tomorrow_goals)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """), (user_id, entry_date, mood, gratitude, highlights, challenges, tomorrow_goals))
    conn.commit()
    conn.close()

def get_daily_entry(user_id, entry_date):
    conn = db.get_connection()
    df = pd.read_sql_query(
        db.convert_sql("SELECT * FROM daily_entries WHERE user_id = ? AND entry_date = ?"),
        conn,
        params=(user_id, entry_date)
    )
    conn.close()
    return df

# AI Assistant Functions
def call_gemini(system_prompt, user_prompt):
    """Call Google Gemini AI using the official SDK"""
    if not GEMINI_AVAILABLE:
        return None, "Google Generative AI library not available"

    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        return None, "API key not configured"

    try:
        # Configure the SDK with the API key
        genai.configure(api_key=api_key)

        # Create the model - use gemini-2.5-flash (latest model)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Generate content
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = model.generate_content(full_prompt)

        return response.text, "success"
    except Exception as e:
        st.error(f"Gemini API Error: {str(e)}")
        return None, f"Error: {str(e)}"

def ai_create_tasks(user_prompt, user_id):
    """Use Google Gemini AI to create tasks from natural language"""
    if not GEMINI_AVAILABLE:
        return 0, "Google Generative AI library not available"

    system_prompt = """You are a productivity assistant. Convert user requests into structured tasks.
    Return ONLY a valid JSON object with a "tasks" key containing an array of task objects.
    Each task must have: title, description, category (Work/Personal/Health/Learning/Finance/Other),
    priority (high/medium/low), due_date (YYYY-MM-DD), estimated_hours (number).

    Example: {"tasks": [{"title": "Finish project report", "description": "Complete and submit",
    "category": "Work", "priority": "high", "due_date": "2025-01-17", "estimated_hours": 3.0}]}
    """

    try:
        # Use the call_gemini function
        response_text, status = call_gemini(system_prompt, user_prompt)

        if not response_text or status != "success":
            return 0, "Failed to get AI response"

        # Parse JSON from response - Gemini sometimes wraps in markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        tasks_data = json.loads(response_text)

        # Add tasks to database
        tasks_added = 0
        for task in tasks_data.get("tasks", []):
            add_task(
                user_id,
                task.get("title", "Untitled Task"),
                task.get("description", ""),
                task.get("category", "Other"),
                task.get("priority", "medium"),
                task.get("due_date", (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")),
                task.get("estimated_hours", 1.0),
                []
            )
            tasks_added += 1

        return tasks_added, f"✅ Successfully created {tasks_added} task(s)!"

    except Exception as e:
        return 0, f"Error creating tasks: {str(e)}"

def ai_productivity_insights(user_id):
    """Generate AI insights using Google Gemini"""
    conn = db.get_connection()
    tasks = pd.read_sql_query(db.convert_sql("""
        SELECT title, category, priority, status,
               DATE(created_at) as created, DATE(completed_at) as completed
        FROM tasks
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    """), conn, params=(user_id,))
    conn.close()

    if tasks.empty:
        return "Not enough data yet. Complete more tasks to get insights!"

    task_summary = f"""User has {len(tasks)} recent tasks:
    - Completed: {len(tasks[tasks['status'] == 'completed'])}
    - Pending: {len(tasks[tasks['status'] == 'pending'])}
    - Categories: {tasks['category'].value_counts().to_dict()}
    - Priorities: {tasks['priority'].value_counts().to_dict()}"""

    response, status = call_gemini(
        "You are a productivity coach. Analyze task patterns and provide 3-4 actionable insights in a friendly tone.",
        task_summary
    )

    return response if response else "Please add your Google Gemini API key to use this feature."

def ai_daily_planner(user_id):
    """AI daily planner using Google Gemini"""
    conn = db.get_connection()
    pending_tasks = pd.read_sql_query(db.convert_sql("""
        SELECT title, category, priority, due_date, estimated_hours
        FROM tasks
        WHERE user_id = ? AND status = 'pending'
        ORDER BY priority DESC, due_date ASC
        LIMIT 20
    """), conn, params=(user_id,))
    conn.close()

    if pending_tasks.empty:
        return "You have no pending tasks! Great job! 🎉"

    context = f"""User has {len(pending_tasks)} pending tasks. Suggest 5-7 to focus on today.
    Tasks:\n{pending_tasks.to_string()}"""

    response, status = call_gemini(
        "You are a productivity planner. Suggest a realistic daily task list. Use emojis and be encouraging.",
        context
    )

    return response if response else "Please add your Google Gemini API key to use this feature."

def ai_chat_assistant(user_prompt, user_id):
    """AI chat assistant using Google Gemini"""
    stats = get_productivity_stats(user_id)

    context = f"""User context - Tasks: {stats['total_tasks']}, Completed: {stats['completed_tasks']},
    Rate: {stats['completion_rate']:.1f}%, Streak: {stats['streak']} days

    User question: {user_prompt}"""

    response, status = call_gemini(
        "You are a helpful productivity assistant. Provide actionable advice based on the user's stats and question.",
        context
    )

    return response if response else "Please add your Google Gemini API key to use this feature."

def show_ai_chat_widget(user_id, context_info=""):
    """Reusable AI chat widget that can be embedded in any tab"""
    if not GEMINI_AVAILABLE:
        return

    # Check if API key is configured
    try:
        if not (hasattr(st, 'secrets') and "GOOGLE_API_KEY" in st.secrets):
            return
    except:
        return

    # AI Assistant section - always visible
    st.markdown("### 🤖 AI Assistant")

    # Special handling for Tasks tab - allow task creation
    if context_info == "tasks":
        st.caption("Create tasks naturally! Example: 'I need to finish the report by Friday and call the dentist tomorrow'")

        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_input(
                "Describe your tasks:",
                placeholder="I need to finish the report by Friday and call the dentist tomorrow",
                key=f"ai_chat_{context_info}",
                label_visibility="collapsed"
            )
        with col2:
            create_button = st.button("Create Tasks", key=f"ai_ask_{context_info}", type="primary", use_container_width=True)

        if create_button and user_input:
            with st.spinner("🤔 Creating your tasks..."):
                num_tasks, message = ai_create_tasks(user_input, user_id)
                if num_tasks > 0:
                    st.success(message)
                    show_fireworks()
                    st.info(f"✅ {num_tasks} task(s) have been added! Check the 'View Tasks' tab below.")
                    # Auto-refresh to show new tasks
                    import time
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(message)
    else:
        # Regular chat for other tabs
        st.caption("Ask me anything about productivity or get help with this section!")

        col1, col2 = st.columns([4, 1])
        with col1:
            user_question = st.text_input(
                "Ask a question:",
                placeholder="How can I improve my productivity? What should I focus on today?",
                key=f"ai_chat_{context_info}",
                label_visibility="collapsed"
            )
        with col2:
            ask_button = st.button("Ask AI", key=f"ai_ask_{context_info}", type="primary", use_container_width=True)

        if ask_button and user_question:
            with st.spinner("🤔 Thinking..."):
                response = ai_chat_assistant(user_question, user_id)
                st.markdown("**💡 AI Response:**")
                st.info(response)

    st.markdown("---")

# Authentication Page
def show_auth_page():
    st.markdown('<h1 class="main-header">🚀 Ultimate Productivity Planner</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="motivational-quote">💭 {get_daily_quote()}</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            remember_me = st.checkbox("Remember me", value=True)
            submit = st.form_submit_button("Login")

            if submit:
                user_id, username_result, is_admin = login_user(username, password)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.username = username_result
                    st.session_state.user_id = user_id
                    st.session_state.is_admin = is_admin
                    st.session_state.remember_me = remember_me

                    # Store credentials in session_state if remember me is checked
                    if remember_me:
                        st.session_state.stored_user_id = user_id
                        st.session_state.stored_username = username_result
                        st.session_state.stored_is_admin = is_admin

                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

    with tab2:
        st.subheader("Create New Account")
        with st.form("signup_form"):
            new_username = st.text_input("Choose Username")
            new_email = st.text_input("Email (optional)")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_signup = st.form_submit_button("Sign Up")

            if submit_signup:
                if new_password != confirm_password:
                    st.error("Passwords don't match!")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                elif len(new_username) < 3:
                    st.error("Username must be at least 3 characters")
                else:
                    if register_user(new_username, new_password, new_email):
                        st.success("Account created! Please login.")
                    else:
                        st.error("Username already exists")

# Main App (modified to use user_id)
def main():
    # Auto-login if remember me was checked previously
    if not st.session_state.logged_in and 'stored_user_id' in st.session_state:
        st.session_state.logged_in = True
        st.session_state.user_id = st.session_state.stored_user_id
        st.session_state.username = st.session_state.stored_username
        st.session_state.is_admin = st.session_state.stored_is_admin
        st.session_state.remember_me = True

    if not st.session_state.logged_in:
        show_auth_page()
        return

    user_id = st.session_state.user_id

    st.markdown('<h1 class="main-header">🚀 Ultimate Productivity Planner</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="motivational-quote">💭 {get_daily_quote()}</div>', unsafe_allow_html=True)

    # Sidebar with logout
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    if st.session_state.is_admin:
        st.sidebar.caption("🔑 Admin")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.is_admin = False
        # Clear stored credentials
        if 'stored_user_id' in st.session_state:
            del st.session_state.stored_user_id
        if 'stored_username' in st.session_state:
            del st.session_state.stored_username
        if 'stored_is_admin' in st.session_state:
            del st.session_state.stored_is_admin
        if 'remember_me' in st.session_state:
            del st.session_state.remember_me
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.title("Navigation")

    # Build navigation menu based on admin status
    nav_options = [
        "📊 Dashboard",
        "✅ Tasks",
        "🎯 Goals",
        "📅 Calendar View",
        "📝 Daily Journal",
        "🏆 Achievements",
        "📈 Analytics",
        "🤖 AI Assistant"
    ]

    # Only show Admin Panel to admins
    if st.session_state.is_admin:
        nav_options.append("👥 Admin Panel")

    page = st.sidebar.radio("Go to", nav_options)

    if page == "📊 Dashboard":
        show_dashboard(user_id)
    elif page == "✅ Tasks":
        show_tasks(user_id)
    elif page == "🎯 Goals":
        show_goals(user_id)
    elif page == "📅 Calendar View":
        show_calendar(user_id)
    elif page == "📝 Daily Journal":
        show_daily_journal(user_id)
    elif page == "🏆 Achievements":
        show_achievements_page(user_id)
    elif page == "📈 Analytics":
        show_analytics(user_id)
    elif page == "🤖 AI Assistant":
        show_ai_assistant(user_id)
    elif page == "👥 Admin Panel":
        show_admin_panel(user_id)

# All the show_* functions remain the same but now accept user_id parameter
# I'll include the key ones here:

def show_dashboard(user_id):
    st.header("📊 Your Productivity Dashboard")

    # AI Assistant Widget
    show_ai_chat_widget(user_id, "dashboard")

    # Get data
    stats = get_productivity_stats(user_id)
    conn = db.get_connection()

    # KPI Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tasks", stats['total_tasks'], delta=f"+{stats['week_completed']} this week")
    with col2:
        st.metric("Completed", stats['completed_tasks'], delta=f"{stats['completion_rate']:.0f}% rate")
    with col3:
        st.metric("Current Streak", f"{stats['streak']} days", delta="🔥" if stats['streak'] > 0 else None)
    with col4:
        next_milestone = next((m for m in [5, 10, 25, 50, 100, 250, 500] if m > stats['completed_tasks']), 1000)
        remaining = next_milestone - stats['completed_tasks']
        st.metric("Next Milestone", f"{next_milestone} tasks", delta=f"{remaining} to go")

    st.markdown("---")

    # Charts Row 1: Quick Overview Charts
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📈 Task Progress")

        # Donut chart for task completion
        completion_data = pd.DataFrame({
            'Status': ['Completed', 'Remaining'],
            'Count': [stats['completed_tasks'], stats['total_tasks'] - stats['completed_tasks']]
        })

        fig_completion = px.pie(
            completion_data,
            values='Count',
            names='Status',
            hole=0.6,
            color_discrete_map={'Completed': '#2ecc71', 'Remaining': '#e0e0e0'}
        )

        fig_completion.update_traces(textposition='inside', textinfo='percent+label')
        fig_completion.update_layout(
            height=250,
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20)
        )

        st.plotly_chart(fig_completion, use_container_width=True)
        st.caption(f"**{stats['completion_rate']:.1f}%** Overall Completion Rate")

    with col2:
        st.subheader("⏰ This Week")

        # Get this week's daily completions
        week_ago = datetime.now() - timedelta(days=7)
        weekly_tasks = pd.read_sql_query(db.convert_sql("""
            SELECT DATE(completed_at) as date, COUNT(*) as count
            FROM tasks
            WHERE user_id = ? AND status = 'completed' AND completed_at >= ?
            GROUP BY DATE(completed_at)
            ORDER BY date
        """), conn, params=(user_id, week_ago.strftime("%Y-%m-%d")))

        if not weekly_tasks.empty:
            fig_week = px.bar(
                weekly_tasks,
                x='date',
                y='count',
                color='count',
                color_continuous_scale='Blues'
            )

            fig_week.update_layout(
                height=250,
                showlegend=False,
                xaxis_title="",
                yaxis_title="Tasks",
                margin=dict(l=20, r=20, t=20, b=20)
            )

            st.plotly_chart(fig_week, use_container_width=True)
            st.caption(f"**{stats['week_completed']}** tasks completed this week")
        else:
            st.info("Complete tasks to see weekly progress!")

    with col3:
        st.subheader("🎯 Goals Progress")

        goals = get_goals(user_id)
        if not goals.empty:
            # Calculate average goal progress
            avg_progress = goals['progress'].mean()

            fig_goals = go.Figure(go.Indicator(
                mode="gauge+number",
                value=avg_progress,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#3498db"},
                    'steps': [
                        {'range': [0, 33], 'color': "#ffe6e6"},
                        {'range': [33, 66], 'color': "#fff4e6"},
                        {'range': [66, 100], 'color': "#e6ffe6"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))

            fig_goals.update_layout(
                height=250,
                margin=dict(l=20, r=20, t=20, b=20)
            )

            st.plotly_chart(fig_goals, use_container_width=True)
            st.caption(f"**{avg_progress:.1f}%** Average Goal Progress")
        else:
            st.info("Set goals to track progress!")

    st.markdown("---")

    # Charts Row 2: Priority & Category Overview
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎨 Tasks by Category")

        category_data = pd.read_sql_query(db.convert_sql("""
            SELECT category, COUNT(*) as count
            FROM tasks
            WHERE user_id = ? AND status != 'completed'
            GROUP BY category
            ORDER BY count DESC
        """), conn, params=(user_id,))

        if not category_data.empty:
            fig_category = px.bar(
                category_data,
                x='count',
                y='category',
                orientation='h',
                color='count',
                color_continuous_scale='Viridis',
                text='count'
            )

            fig_category.update_traces(textposition='outside')
            fig_category.update_layout(
                height=300,
                showlegend=False,
                xaxis_title="Active Tasks",
                yaxis_title="",
                margin=dict(l=20, r=20, t=20, b=20)
            )

            st.plotly_chart(fig_category, use_container_width=True)
        else:
            st.info("Add tasks to see category breakdown!")

    with col2:
        st.subheader("🚦 Priority Distribution")

        priority_data = pd.read_sql_query(db.convert_sql("""
            SELECT priority, COUNT(*) as count
            FROM tasks
            WHERE user_id = ? AND status != 'completed'
            GROUP BY priority
        """), conn, params=(user_id,))

        if not priority_data.empty:
            priority_colors = {'high': '#e74c3c', 'medium': '#f39c12', 'low': '#2ecc71'}

            fig_priority = px.pie(
                priority_data,
                values='count',
                names='priority',
                color='priority',
                color_discrete_map=priority_colors,
                hole=0.4
            )

            fig_priority.update_traces(textposition='inside', textinfo='percent+label')
            fig_priority.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20)
            )

            st.plotly_chart(fig_priority, use_container_width=True)

            # Priority alert
            high_priority_count = priority_data[priority_data['priority'] == 'high']['count'].sum() if 'high' in priority_data['priority'].values else 0
            if high_priority_count > 0:
                st.warning(f"⚠️ {high_priority_count} high-priority tasks need attention!")
        else:
            st.info("Add tasks to see priority breakdown!")

    st.markdown("---")

    # Tasks and Goals Section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📋 Today's Urgent Tasks")
        today_tasks = get_tasks(user_id, status='pending')
        if not today_tasks.empty:
            today_tasks['due_date'] = pd.to_datetime(today_tasks['due_date'])
            urgent_tasks = today_tasks[today_tasks['due_date'] <= pd.Timestamp(datetime.now().date())]
            if not urgent_tasks.empty:
                for _, task in urgent_tasks.head(5).iterrows():
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        priority_emoji = "🔴" if task['priority'] == 'high' else "🟡" if task['priority'] == 'medium' else "🟢"
                        st.write(f"{priority_emoji} **{task['title']}** - Due: {task['due_date'].strftime('%Y-%m-%d')}")
                    with col_b:
                        if st.button("✓", key=f"complete_dash_{task['id']}"):
                            update_task_status(user_id, task['id'], 'completed')
                            st.success("🎉 Task Completed!")
                            show_fireworks()
                            import time
                            time.sleep(2)
                            st.rerun()
            else:
                st.success("🎉 No urgent tasks! You're doing great!")
        else:
            st.info("No pending tasks. Time to add some goals!")

    with col2:
        st.subheader("🎯 Active Goals")
        goals = get_goals(user_id)
        if not goals.empty:
            for _, goal in goals.head(3).iterrows():
                st.write(f"**{goal['title']}**")
                st.progress(goal['progress'] / 100)
                st.caption(f"{goal['progress']}% complete")
        else:
            st.info("No active goals. Set some in the Goals section!")

    conn.close()

def show_tasks(user_id):
    st.header("✅ Task Management")

    # AI Assistant Widget
    show_ai_chat_widget(user_id, "tasks")

    tab1, tab2 = st.tabs(["📝 Add Task", "📋 View Tasks"])

    with tab1:
        with st.form("add_task_form"):
            st.subheader("Create New Task")
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Task Title*")
                category = st.selectbox("Category", ["Work", "Personal", "Health", "Learning", "Finance", "Other"])
                priority = st.selectbox("Priority", ["high", "medium", "low"])
            with col2:
                due_date = st.date_input("Due Date", value=datetime.now() + timedelta(days=1))
                estimated_hours = st.number_input("Estimated Hours", min_value=0.0, max_value=100.0, value=1.0, step=0.5)
                tags_input = st.text_input("Tags (comma-separated)")
            description = st.text_area("Description")
            submitted = st.form_submit_button("➕ Add Task", use_container_width=True)

            if submitted and title:
                tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
                add_task(user_id, title, description, category, priority, due_date.strftime("%Y-%m-%d"), estimated_hours, tags)
                st.success(f"✅ **Task Added!** '{title}' has been successfully added to your task list.")
                show_fireworks()
                st.info("Redirecting to task list...")
                import time
                time.sleep(2)
                st.rerun()
            elif submitted and not title:
                st.error("❌ Please enter a task title!")

    with tab2:
        st.subheader("Your Tasks")
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["all", "pending", "in_progress", "completed"])
        with col2:
            category_filter = st.selectbox("Filter by Category", ["all", "Work", "Personal", "Health", "Learning", "Finance", "Other"])

        tasks = get_tasks(
            user_id,
            status=None if status_filter == "all" else status_filter,
            category=None if category_filter == "all" else category_filter
        )

        if not tasks.empty:
            tasks['due_date'] = pd.to_datetime(tasks['due_date'])
            for _, task in tasks.iterrows():
                with st.expander(f"{task['title']} - {task['category']} ({task['priority']} priority)"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Description:** {task['description']}")
                        st.write(f"**Due Date:** {task['due_date'].strftime('%Y-%m-%d')}")
                        st.write(f"**Status:** {task['status']}")
                    with col2:
                        if task['status'] != 'completed':
                            if st.button("✓ Complete", key=f"complete_{task['id']}"):
                                update_task_status(user_id, task['id'], 'completed')
                                st.success(f"🎉 **Task Completed!** Great job on '{task['title']}'!")
                                show_fireworks()
                                import time
                                time.sleep(2)
                                st.rerun()

                        # Edit button
                        if st.button("✏️ Edit", key=f"edit_{task['id']}"):
                            st.session_state[f'editing_{task["id"]}'] = True
                            st.rerun()

                        if st.button("🗑️ Delete", key=f"delete_{task['id']}"):
                            delete_task(user_id, task['id'])
                            st.warning(f"Task '{task['title']}' deleted")
                            st.rerun()

                    # Edit form (shown when edit button is clicked)
                    if st.session_state.get(f'editing_{task["id"]}', False):
                        st.markdown("---")
                        st.subheader("✏️ Edit Task")

                        with st.form(key=f"edit_form_{task['id']}"):
                            edit_col1, edit_col2 = st.columns(2)

                            with edit_col1:
                                edit_title = st.text_input("Title", value=task['title'])
                                edit_category = st.selectbox("Category",
                                    ["Work", "Personal", "Health", "Learning", "Finance", "Other"],
                                    index=["Work", "Personal", "Health", "Learning", "Finance", "Other"].index(task['category']))
                                edit_priority = st.selectbox("Priority",
                                    ["high", "medium", "low"],
                                    index=["high", "medium", "low"].index(task['priority']))

                            with edit_col2:
                                edit_due_date = st.date_input("Due Date", value=task['due_date'])
                                edit_estimated_hours = st.number_input("Estimated Hours",
                                    value=float(task['estimated_hours']) if task['estimated_hours'] else 1.0,
                                    min_value=0.0, max_value=100.0, step=0.5)
                                edit_status = st.selectbox("Status",
                                    ["pending", "in_progress", "completed"],
                                    index=["pending", "in_progress", "completed"].index(task['status']))

                            edit_description = st.text_area("Description", value=task['description'] if task['description'] else "")

                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                save_changes = st.form_submit_button("💾 Save Changes", use_container_width=True)
                            with col_cancel:
                                cancel_edit = st.form_submit_button("❌ Cancel", use_container_width=True)

                            if save_changes:
                                # Update the task in database
                                conn = db.get_connection()
                                cursor = conn.cursor()
                                cursor.execute(db.convert_sql("""
                                    UPDATE tasks
                                    SET title=?, description=?, category=?, priority=?,
                                        due_date=?, estimated_hours=?, status=?
                                    WHERE id=? AND user_id=?
                                """), (edit_title, edit_description, edit_category, edit_priority,
                                       edit_due_date.strftime("%Y-%m-%d"), edit_estimated_hours,
                                       edit_status, task['id'], user_id))
                                conn.commit()
                                conn.close()

                                st.success("✅ Task updated successfully!")
                                del st.session_state[f'editing_{task["id"]}']
                                st.rerun()

                            if cancel_edit:
                                del st.session_state[f'editing_{task["id"]}']
                                st.rerun()
        else:
            st.info("No tasks found. Add your first task above!")

def show_goals(user_id):
    st.header("🎯 Goal Tracking")

    # AI Assistant Widget
    show_ai_chat_widget(user_id, "goals")

    tab1, tab2 = st.tabs(["➕ Add Goal", "📊 View Goals"])

    with tab1:
        with st.form("add_goal_form"):
            st.subheader("Set a New Goal")
            title = st.text_input("Goal Title*")
            description = st.text_area("Description")
            target_date = st.date_input("Target Date", value=datetime.now() + timedelta(days=30))
            submitted = st.form_submit_button("🎯 Add Goal", use_container_width=True)

            if submitted and title:
                add_goal(user_id, title, description, target_date.strftime("%Y-%m-%d"))
                st.success(f"🎯 Goal '{title}' created!")
                st.rerun()

    with tab2:
        st.subheader("Your Goals")
        goals = get_goals(user_id)
        if not goals.empty:
            for _, goal in goals.iterrows():
                with st.expander(f"{goal['title']} - {goal['progress']}% Complete"):
                    st.write(f"**Description:** {goal['description']}")
                    st.write(f"**Target Date:** {goal['target_date']}")
                    new_progress = st.slider("Update Progress", 0, 100, int(goal['progress']), key=f"progress_slider_{goal['id']}")
                    if st.button("💾 Update Progress", key=f"update_{goal['id']}"):
                        update_goal_progress(user_id, goal['id'], new_progress)
                        st.success("Progress updated!")
                        st.rerun()
        else:
            st.info("No goals yet. Set your first goal above!")

def show_calendar(user_id):
    st.header("📅 Calendar View")
    tasks = get_tasks(user_id)
    if not tasks.empty:
        tasks['due_date'] = pd.to_datetime(tasks['due_date'])
        fig = px.timeline(tasks, x_start="created_at", x_end="due_date", y="title", color="priority",
                         color_discrete_map={"high": "#ef4444", "medium": "#f59e0b", "low": "#10b981"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tasks to display!")

def show_daily_journal(user_id):
    st.header("📝 Daily Journal & Reflection")

    # AI Assistant Widget
    show_ai_chat_widget(user_id, "journal")

    col1, col2 = st.columns([2, 1])

    with col1:
        entry_date = st.date_input("📅 Select Date", value=datetime.now())

    with col2:
        st.markdown("### Quick Stats")
        conn = db.get_connection()
        total_entries = pd.read_sql_query(db.convert_sql("""
            SELECT COUNT(*) as count FROM daily_entries WHERE user_id = ?
        """), conn, params=(user_id,)).iloc[0]['count']
        conn.close()
        st.metric("Journal Entries", total_entries)

    entry_date_str = entry_date.strftime("%Y-%m-%d")
    existing_entry = get_daily_entry(user_id, entry_date_str)

    st.markdown("---")

    with st.form("daily_journal_form"):
        st.subheader("How are you feeling today?")

        # Enhanced mood selector with emojis and descriptions
        mood_options = {
            1: "😢 Very Bad - Struggling today",
            2: "😕 Bad - Not feeling great",
            3: "😐 Neutral - Just okay",
            4: "🙂 Good - Feeling positive",
            5: "😊 Great - Feeling amazing!"
        }

        # Get existing mood or default to 3
        existing_mood = int(existing_entry.iloc[0]['mood']) if not existing_entry.empty and existing_entry.iloc[0]['mood'] else 3
        # Ensure existing mood is in valid range
        if existing_mood < 1 or existing_mood > 5:
            existing_mood = 3

        # Create radio buttons for mood selection
        mood_selection = st.radio(
            "Rate your mood:",
            options=list(mood_options.keys()),
            format_func=lambda x: mood_options[x],
            index=existing_mood - 1,
            horizontal=True
        )

        st.markdown("---")

        # Journal sections in columns
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🙏 Gratitude")
            st.caption("What are you thankful for today?")
            gratitude = st.text_area(
                "Gratitude",
                value=existing_entry.iloc[0]['gratitude'] if not existing_entry.empty else "",
                height=120,
                placeholder="I'm grateful for...",
                label_visibility="collapsed"
            )

            st.markdown("### ✨ Highlights")
            st.caption("What went well today?")
            highlights = st.text_area(
                "Highlights",
                value=existing_entry.iloc[0]['highlights'] if not existing_entry.empty else "",
                height=120,
                placeholder="Today's wins and positive moments...",
                label_visibility="collapsed"
            )

        with col2:
            st.markdown("### 💪 Challenges")
            st.caption("What was difficult today?")
            challenges = st.text_area(
                "Challenges",
                value=existing_entry.iloc[0]['challenges'] if not existing_entry.empty else "",
                height=120,
                placeholder="What I struggled with...",
                label_visibility="collapsed"
            )

            st.markdown("### 🎯 Tomorrow's Goals")
            st.caption("What do you want to accomplish?")
            tomorrow_goals = st.text_area(
                "Tomorrow's Goals",
                value=existing_entry.iloc[0]['tomorrow_goals'] if not existing_entry.empty else "",
                height=120,
                placeholder="Tomorrow I will...",
                label_visibility="collapsed"
            )

        st.markdown("---")

        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button("💾 Save Journal Entry", use_container_width=True, type="primary")

        if submitted:
            save_daily_entry(user_id, entry_date_str, mood_selection, gratitude, highlights, challenges, tomorrow_goals)
            st.success("✅ Journal entry saved successfully!")
            show_fireworks()

    # Show recent entries
    if not existing_entry.empty:
        st.markdown("---")
        st.subheader("📖 Your Entry for " + entry_date.strftime("%B %d, %Y"))

        mood_emoji = {1: '😢', 2: '😕', 3: '😐', 4: '🙂', 5: '😊'}
        entry_mood = int(existing_entry.iloc[0]['mood']) if existing_entry.iloc[0]['mood'] else 3
        if entry_mood in mood_emoji:
            st.markdown(f"**Mood:** {mood_emoji[entry_mood]} {mood_options.get(entry_mood, 'N/A')}")

        if existing_entry.iloc[0]['gratitude']:
            st.markdown(f"**🙏 Gratitude:** {existing_entry.iloc[0]['gratitude']}")
        if existing_entry.iloc[0]['highlights']:
            st.markdown(f"**✨ Highlights:** {existing_entry.iloc[0]['highlights']}")
        if existing_entry.iloc[0]['challenges']:
            st.markdown(f"**💪 Challenges:** {existing_entry.iloc[0]['challenges']}")
        if existing_entry.iloc[0]['tomorrow_goals']:
            st.markdown(f"**🎯 Tomorrow's Goals:** {existing_entry.iloc[0]['tomorrow_goals']}")

def show_achievements_page(user_id):
    st.header("🏆 Achievements & Milestones")

    # AI Assistant Widget
    show_ai_chat_widget(user_id, "achievements")

    achievements = get_achievements(user_id)

    if not achievements.empty:
        for _, achievement in achievements.iterrows():
            st.markdown(f'<div class="achievement-badge">{achievement["icon"]} {achievement["name"]} - {achievement["description"]}</div>', unsafe_allow_html=True)
    else:
        st.info("Complete tasks to earn achievements!")

def show_analytics(user_id):
    st.header("📈 Productivity Analytics & Insights")

    # AI Assistant Widget
    show_ai_chat_widget(user_id, "analytics")

    # Get all data
    stats = get_productivity_stats(user_id)
    conn = db.get_connection()

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tasks", stats['total_tasks'],
                 delta=f"+{stats['week_completed']} this week")
    with col2:
        st.metric("Completion Rate", f"{stats['completion_rate']:.1f}%",
                 delta="Outstanding!" if stats['completion_rate'] >= 80 else "Keep going!")
    with col3:
        st.metric("Tasks This Week", stats['week_completed'])
    with col4:
        st.metric("Current Streak", f"{stats['streak']} days",
                 delta="🔥" if stats['streak'] > 0 else None)

    st.markdown("---")

    # Get task data for charts
    all_tasks = pd.read_sql_query(db.convert_sql("""
        SELECT title, category, priority, status, due_date, completed_at, created_at, estimated_hours
        FROM tasks
        WHERE user_id = ?
        ORDER BY created_at DESC
    """), conn, params=(user_id,))

    if not all_tasks.empty:
        # Convert dates
        all_tasks['due_date'] = pd.to_datetime(all_tasks['due_date'])
        all_tasks['completed_at'] = pd.to_datetime(all_tasks['completed_at'])
        all_tasks['created_at'] = pd.to_datetime(all_tasks['created_at'])

        # Row 1: Task Distribution Charts
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Tasks by Category")
            category_counts = all_tasks['category'].value_counts().reset_index()
            category_counts.columns = ['category', 'count']

            fig_category = px.pie(
                category_counts,
                values='count',
                names='category',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_category.update_traces(textposition='inside', textinfo='percent+label')
            fig_category.update_layout(height=350, showlegend=True)
            st.plotly_chart(fig_category, use_container_width=True)

        with col2:
            st.subheader("🎯 Tasks by Priority")
            priority_counts = all_tasks['priority'].value_counts().reset_index()
            priority_counts.columns = ['priority', 'count']

            # Define colors for priorities
            priority_colors = {'high': '#FF6B6B', 'medium': '#FFD93D', 'low': '#6BCB77'}

            fig_priority = px.bar(
                priority_counts,
                x='priority',
                y='count',
                color='priority',
                color_discrete_map=priority_colors,
                text='count'
            )
            fig_priority.update_traces(textposition='outside')
            fig_priority.update_layout(
                height=350,
                showlegend=False,
                xaxis_title="Priority Level",
                yaxis_title="Number of Tasks"
            )
            st.plotly_chart(fig_priority, use_container_width=True)

        st.markdown("---")

        # Row 2: Completion Status and Timeline
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("✅ Completion Status")
            status_counts = all_tasks['status'].value_counts().reset_index()
            status_counts.columns = ['status', 'count']

            status_colors = {'completed': '#4CAF50', 'pending': '#FFC107', 'in_progress': '#2196F3'}

            fig_status = px.bar(
                status_counts,
                x='status',
                y='count',
                color='status',
                color_discrete_map=status_colors,
                text='count'
            )
            fig_status.update_traces(textposition='outside')
            fig_status.update_layout(
                height=350,
                showlegend=False,
                xaxis_title="Status",
                yaxis_title="Number of Tasks"
            )
            st.plotly_chart(fig_status, use_container_width=True)

        with col2:
            st.subheader("📅 Completion Timeline")
            completed_tasks = all_tasks[all_tasks['status'] == 'completed'].copy()

            if not completed_tasks.empty:
                completed_tasks['completion_date'] = completed_tasks['completed_at'].dt.date
                daily_completions = completed_tasks.groupby('completion_date').size().reset_index()
                daily_completions.columns = ['date', 'tasks_completed']

                fig_timeline = px.line(
                    daily_completions,
                    x='date',
                    y='tasks_completed',
                    markers=True,
                    line_shape='spline'
                )
                fig_timeline.update_traces(
                    line_color='#667eea',
                    marker=dict(size=8, color='#764ba2')
                )
                fig_timeline.update_layout(
                    height=350,
                    xaxis_title="Date",
                    yaxis_title="Tasks Completed",
                    hovermode='x unified'
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            else:
                st.info("Complete some tasks to see your completion timeline!")

        st.markdown("---")

        # Row 3: Advanced Analytics
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("⏰ Estimated Hours by Category")
            tasks_with_hours = all_tasks[all_tasks['estimated_hours'].notna()].copy()

            if not tasks_with_hours.empty:
                hours_by_category = tasks_with_hours.groupby('category')['estimated_hours'].sum().reset_index()
                hours_by_category.columns = ['category', 'total_hours']

                fig_hours = px.bar(
                    hours_by_category,
                    x='category',
                    y='total_hours',
                    color='total_hours',
                    color_continuous_scale='Viridis',
                    text='total_hours'
                )
                fig_hours.update_traces(texttemplate='%{text:.1f}h', textposition='outside')
                fig_hours.update_layout(
                    height=350,
                    xaxis_title="Category",
                    yaxis_title="Total Hours",
                    showlegend=False
                )
                st.plotly_chart(fig_hours, use_container_width=True)
            else:
                st.info("Add estimated hours to tasks to see time allocation!")

        with col2:
            st.subheader("📈 Weekly Productivity Trend")

            # Get last 8 weeks of data
            eight_weeks_ago = datetime.now() - timedelta(weeks=8)
            recent_completed = all_tasks[
                (all_tasks['status'] == 'completed') &
                (all_tasks['completed_at'] >= eight_weeks_ago)
            ].copy()

            if not recent_completed.empty:
                recent_completed['week'] = recent_completed['completed_at'].dt.to_period('W').astype(str)
                weekly_counts = recent_completed.groupby('week').size().reset_index()
                weekly_counts.columns = ['week', 'tasks_completed']

                fig_weekly = px.area(
                    weekly_counts,
                    x='week',
                    y='tasks_completed',
                    line_shape='spline'
                )
                fig_weekly.update_traces(
                    fill='tozeroy',
                    line_color='#667eea',
                    fillcolor='rgba(102, 126, 234, 0.3)'
                )
                fig_weekly.update_layout(
                    height=350,
                    xaxis_title="Week",
                    yaxis_title="Tasks Completed",
                    hovermode='x unified'
                )
                st.plotly_chart(fig_weekly, use_container_width=True)
            else:
                st.info("Complete tasks over multiple weeks to see trends!")

        st.markdown("---")

        # Row 4: Heatmap of productivity
        st.subheader("🔥 Productivity Heatmap (Last 30 Days)")

        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_tasks = all_tasks[
            (all_tasks['status'] == 'completed') &
            (all_tasks['completed_at'] >= thirty_days_ago)
        ].copy()

        if not recent_tasks.empty:
            recent_tasks['date'] = recent_tasks['completed_at'].dt.date
            recent_tasks['weekday'] = recent_tasks['completed_at'].dt.day_name()
            recent_tasks['week'] = recent_tasks['completed_at'].dt.isocalendar().week

            heatmap_data = recent_tasks.groupby(['week', 'weekday']).size().reset_index()
            heatmap_data.columns = ['week', 'weekday', 'count']

            # Pivot for heatmap
            heatmap_pivot = heatmap_data.pivot(index='weekday', columns='week', values='count').fillna(0)

            # Reorder days
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            heatmap_pivot = heatmap_pivot.reindex([d for d in days_order if d in heatmap_pivot.index])

            fig_heatmap = px.imshow(
                heatmap_pivot,
                labels=dict(x="Week", y="Day of Week", color="Tasks Completed"),
                color_continuous_scale='YlOrRd',
                aspect='auto'
            )
            fig_heatmap.update_layout(height=300)
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("Complete tasks over the next 30 days to see your productivity heatmap!")

        # Performance insights
        st.markdown("---")
        st.subheader("💡 Insights & Recommendations")

        insights_col1, insights_col2 = st.columns(2)

        with insights_col1:
            # Most productive category
            if not all_tasks[all_tasks['status'] == 'completed'].empty:
                top_category = all_tasks[all_tasks['status'] == 'completed']['category'].mode()
                if not top_category.empty:
                    st.success(f"🌟 Your most productive category: **{top_category[0]}**")

                # Completion speed
                completed_with_dates = all_tasks[
                    (all_tasks['status'] == 'completed') &
                    (all_tasks['completed_at'].notna()) &
                    (all_tasks['created_at'].notna())
                ].copy()

                if not completed_with_dates.empty:
                    completed_with_dates['completion_time'] = (
                        completed_with_dates['completed_at'] - completed_with_dates['created_at']
                    ).dt.total_seconds() / 3600 / 24  # Convert to days

                    avg_completion_days = completed_with_dates['completion_time'].mean()
                    st.info(f"⏱️ Average task completion time: **{avg_completion_days:.1f} days**")

        with insights_col2:
            # Priority distribution insight
            high_priority_count = len(all_tasks[all_tasks['priority'] == 'high'])
            pending_high_priority = len(all_tasks[(all_tasks['priority'] == 'high') & (all_tasks['status'] == 'pending')])

            if pending_high_priority > 0:
                st.warning(f"⚠️ You have **{pending_high_priority}** pending high-priority tasks!")

            # Overdue tasks
            overdue = all_tasks[
                (all_tasks['status'] != 'completed') &
                (all_tasks['due_date'] < pd.Timestamp(datetime.now().date()))
            ]

            if not overdue.empty:
                st.error(f"🚨 You have **{len(overdue)}** overdue tasks!")
            else:
                st.success("✅ No overdue tasks - you're on track!")

    else:
        st.info("📊 Start adding tasks to see beautiful analytics and insights!")
        st.markdown("""
        Your analytics dashboard will show:
        - 📊 Task distribution by category and priority
        - ✅ Completion status overview
        - 📈 Productivity trends over time
        - 🔥 Heatmap of your most productive days
        - 💡 Personalized insights and recommendations
        """)

    # Journal & Mood Analytics Section
    st.markdown("---")
    st.header("🧠 Journal & Mood Analytics")

    journal_entries = pd.read_sql_query(db.convert_sql("""
        SELECT entry_date, mood, gratitude, highlights, challenges
        FROM daily_entries
        WHERE user_id = ?
        ORDER BY entry_date DESC
    """), conn, params=(user_id,))

    if not journal_entries.empty:
        journal_entries['entry_date'] = pd.to_datetime(journal_entries['entry_date'])

        # Row 1: Mood tracking
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("😊 Mood Trends Over Time")

            # Filter out entries with mood data and validate mood range (1-5)
            mood_data = journal_entries[journal_entries['mood'].notna()].copy()
            mood_data = mood_data[(mood_data['mood'] >= 1) & (mood_data['mood'] <= 5)]

            if not mood_data.empty:
                fig_mood = px.line(
                    mood_data,
                    x='entry_date',
                    y='mood',
                    markers=True,
                    line_shape='spline'
                )

                # Add mood emoji markers
                mood_emojis = {1: '😢', 2: '😕', 3: '😐', 4: '🙂', 5: '😊'}

                fig_mood.update_traces(
                    line_color='#9b59b6',
                    marker=dict(size=10, color='#e74c3c', line=dict(width=2, color='white'))
                )

                fig_mood.update_layout(
                    height=350,
                    xaxis_title="Date",
                    yaxis_title="Mood Rating",
                    yaxis=dict(tickmode='linear', tick0=1, dtick=1, range=[0.5, 5.5]),
                    hovermode='x unified'
                )

                # Add horizontal line for average mood
                avg_mood = mood_data['mood'].mean()
                fig_mood.add_hline(
                    y=avg_mood,
                    line_dash="dash",
                    line_color="green",
                    annotation_text=f"Average: {avg_mood:.1f}",
                    annotation_position="right"
                )

                st.plotly_chart(fig_mood, use_container_width=True)

                # Mood insights
                current_mood_trend = mood_data.head(7)['mood'].mean()
                previous_mood_trend = mood_data.iloc[7:14]['mood'].mean() if len(mood_data) > 7 else None

                if previous_mood_trend:
                    mood_change = current_mood_trend - previous_mood_trend
                    if mood_change > 0.3:
                        st.success(f"📈 Your mood is trending upward! (+{mood_change:.1f} from last week)")
                    elif mood_change < -0.3:
                        st.warning(f"📉 Your mood has decreased recently ({mood_change:.1f} from last week)")
                    else:
                        st.info(f"😌 Your mood is stable (±{abs(mood_change):.1f} from last week)")

            else:
                st.info("Add mood ratings to your journal entries to see mood trends!")

        with col2:
            st.subheader("📊 Mood Distribution")

            if not mood_data.empty:
                mood_counts = mood_data['mood'].value_counts().sort_index().reset_index()
                mood_counts.columns = ['mood', 'count']

                # Map mood numbers to emojis
                mood_labels = {1: '1 - 😢 Very Bad', 2: '2 - 😕 Bad', 3: '3 - 😐 Neutral', 4: '4 - 🙂 Good', 5: '5 - 😊 Great'}
                mood_counts['mood_label'] = mood_counts['mood'].map(mood_labels)

                mood_colors_scale = ['#e74c3c', '#e67e22', '#f39c12', '#27ae60', '#2ecc71']

                fig_mood_dist = px.bar(
                    mood_counts,
                    x='mood_label',
                    y='count',
                    color='mood',
                    color_continuous_scale=mood_colors_scale,
                    text='count'
                )

                fig_mood_dist.update_traces(textposition='outside')
                fig_mood_dist.update_layout(
                    height=350,
                    xaxis_title="Mood Rating",
                    yaxis_title="Number of Days",
                    showlegend=False,
                    xaxis_tickangle=-45
                )

                st.plotly_chart(fig_mood_dist, use_container_width=True)

                # Most common mood
                most_common_mood = mood_data['mood'].mode()
                if not most_common_mood.empty:
                    mood_value = int(most_common_mood[0])
                    if mood_value in mood_labels:
                        mood_emoji = mood_labels[mood_value]
                        st.info(f"🎭 Your most common mood: **{mood_emoji}**")

            else:
                st.info("Add mood ratings to see your mood distribution!")

        st.markdown("---")

        # Row 2: Gratitude & Sentiment Analysis
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🙏 Gratitude Journal Insights")

            gratitude_entries = journal_entries[journal_entries['gratitude'].notna()].copy()

            if not gratitude_entries.empty:
                # Count gratitude entries over time
                gratitude_entries['month'] = gratitude_entries['entry_date'].dt.to_period('M').astype(str)
                gratitude_by_month = gratitude_entries.groupby('month').size().reset_index()
                gratitude_by_month.columns = ['month', 'count']

                fig_gratitude = px.bar(
                    gratitude_by_month,
                    x='month',
                    y='count',
                    color='count',
                    color_continuous_scale='Teal',
                    text='count'
                )

                fig_gratitude.update_traces(textposition='outside')
                fig_gratitude.update_layout(
                    height=300,
                    xaxis_title="Month",
                    yaxis_title="Gratitude Entries",
                    showlegend=False
                )

                st.plotly_chart(fig_gratitude, use_container_width=True)

                # Gratitude stats
                total_gratitude = len(gratitude_entries)
                st.success(f"✨ You've expressed gratitude **{total_gratitude}** times!")

                # Simple word frequency analysis
                all_gratitude_text = ' '.join(gratitude_entries['gratitude'].astype(str).str.lower())
                positive_words = ['happy', 'love', 'grateful', 'thankful', 'blessed', 'amazing', 'wonderful', 'great', 'joy', 'appreciate']
                word_counts = {word: all_gratitude_text.count(word) for word in positive_words}
                top_positive_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:3]

                if top_positive_words[0][1] > 0:
                    st.info(f"💭 Your most used gratitude words: **{', '.join([w[0] for w in top_positive_words if w[1] > 0])}**")

            else:
                st.info("Start adding gratitude entries to track your thankfulness!")

        with col2:
            st.subheader("⭐ Highlights vs Challenges")

            highlights_count = journal_entries[journal_entries['highlights'].notna()].shape[0]
            challenges_count = journal_entries[journal_entries['challenges'].notna()].shape[0]

            highlight_challenge_data = pd.DataFrame({
                'type': ['Highlights 🌟', 'Challenges ⚠️'],
                'count': [highlights_count, challenges_count]
            })

            fig_hl_ch = px.bar(
                highlight_challenge_data,
                x='type',
                y='count',
                color='type',
                color_discrete_map={'Highlights 🌟': '#3498db', 'Challenges ⚠️': '#e67e22'},
                text='count'
            )

            fig_hl_ch.update_traces(textposition='outside')
            fig_hl_ch.update_layout(
                height=300,
                xaxis_title="",
                yaxis_title="Number of Entries",
                showlegend=False
            )

            st.plotly_chart(fig_hl_ch, use_container_width=True)

            # Positivity ratio
            if highlights_count + challenges_count > 0:
                positivity_ratio = highlights_count / (highlights_count + challenges_count) * 100
                if positivity_ratio >= 60:
                    st.success(f"🌈 Great positivity ratio: **{positivity_ratio:.0f}%** highlights!")
                elif positivity_ratio >= 40:
                    st.info(f"⚖️ Balanced outlook: **{positivity_ratio:.0f}%** highlights")
                else:
                    st.warning(f"💪 Stay strong! **{positivity_ratio:.0f}%** highlights - focus on the positives!")

        st.markdown("---")

        # Row 3: Mood-Productivity Correlation
        st.subheader("🔗 Mood & Productivity Correlation")

        # Get tasks completed on journal days
        mood_productivity_data = mood_data.copy()

        if not mood_productivity_data.empty and not all_tasks.empty:
            # Count completed tasks per day
            completed_by_day = all_tasks[all_tasks['status'] == 'completed'].copy()
            if not completed_by_day.empty and 'completed_at' in completed_by_day.columns:
                completed_by_day['completion_date'] = completed_by_day['completed_at'].dt.date
                tasks_per_day = completed_by_day.groupby('completion_date').size().reset_index()
                tasks_per_day.columns = ['date', 'tasks_completed']

                # Merge with mood data
                mood_productivity_data['date'] = mood_productivity_data['entry_date'].dt.date
                merged_data = mood_productivity_data.merge(tasks_per_day, on='date', how='left')
                merged_data['tasks_completed'] = merged_data['tasks_completed'].fillna(0)

                if not merged_data.empty and merged_data['tasks_completed'].sum() > 0:
                    fig_correlation = px.scatter(
                        merged_data,
                        x='mood',
                        y='tasks_completed',
                        size='tasks_completed',
                        color='mood',
                        color_continuous_scale='Viridis',
                        trendline='ols',
                        labels={'mood': 'Mood Rating', 'tasks_completed': 'Tasks Completed'}
                    )

                    fig_correlation.update_layout(
                        height=350,
                        xaxis=dict(tickmode='linear', tick0=1, dtick=1)
                    )

                    st.plotly_chart(fig_correlation, use_container_width=True)

                    # Calculate correlation
                    correlation = merged_data[['mood', 'tasks_completed']].corr().iloc[0, 1]

                    if abs(correlation) > 0.5:
                        if correlation > 0:
                            st.success(f"📈 Strong positive correlation! Better mood = More productivity (r={correlation:.2f})")
                        else:
                            st.info(f"📊 Interesting pattern: Lower mood correlates with higher productivity (r={correlation:.2f})")
                    else:
                        st.info(f"📊 Weak correlation between mood and productivity (r={correlation:.2f})")
                else:
                    st.info("Complete more tasks on days you journal to see mood-productivity correlation!")
            else:
                st.info("Complete tasks to see the correlation between mood and productivity!")
        else:
            st.info("Add journal entries with mood ratings and complete tasks to see correlations!")

        # Summary insights
        st.markdown("---")
        st.subheader("💭 Journal Summary")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Journal Entries", len(journal_entries))

        with col2:
            if not mood_data.empty:
                avg_mood = mood_data['mood'].mean()
                mood_emoji = {1: '😢', 2: '😕', 3: '😐', 4: '🙂', 5: '😊'}
                closest_mood = min(mood_emoji.keys(), key=lambda x: abs(x - avg_mood))
                st.metric("Average Mood", f"{avg_mood:.1f} {mood_emoji[closest_mood]}")
            else:
                st.metric("Average Mood", "N/A")

        with col3:
            consecutive_days = 0
            if not journal_entries.empty:
                sorted_dates = journal_entries['entry_date'].dt.date.sort_values(ascending=False).unique()
                for i in range(len(sorted_dates) - 1):
                    if (sorted_dates[i] - sorted_dates[i + 1]).days == 1:
                        consecutive_days += 1
                    else:
                        break
                consecutive_days += 1 if len(sorted_dates) > 0 else 0

            st.metric("Journal Streak", f"{consecutive_days} days")

    else:
        st.info("📝 Start journaling to see mood analytics, gratitude insights, and emotional well-being trends!")
        st.markdown("""
        Your journal analytics will show:
        - 😊 Mood trends and patterns over time
        - 📊 Mood distribution analysis
        - 🙏 Gratitude journaling insights
        - ⭐ Highlights vs challenges ratio
        - 🔗 Mood-productivity correlation
        - 💭 Journal streaks and summaries
        """)

    conn.close()

def show_admin_panel(user_id):
    st.header("👥 Admin Panel - User Management")

    # Check if user is admin
    if not st.session_state.is_admin:
        st.error("🚫 Access Denied: Admin privileges required")
        st.warning("This page is only accessible to administrators.")
        return

    st.info("📊 View all registered users and database statistics")

    # Check if running on Streamlit Cloud
    if os.getenv('STREAMLIT_SHARING_MODE') or os.getenv('STREAMLIT_RUNTIME_ENV') == 'cloud':
        st.warning("⚠️ **Streamlit Cloud Limitation**: User deletion may not work on Streamlit Community Cloud due to ephemeral filesystem. For full admin functionality, consider running locally or using a PostgreSQL database.")

    conn = db.get_connection()

    # Get all users
    users = pd.read_sql_query("""
        SELECT id, username, email, created_at
        FROM users
        ORDER BY created_at DESC
    """, conn)

    # Display user count
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", len(users))
    with col2:
        total_tasks = pd.read_sql_query("SELECT COUNT(*) as count FROM tasks", conn).iloc[0]['count']
        st.metric("Total Tasks", total_tasks)
    with col3:
        total_goals = pd.read_sql_query("SELECT COUNT(*) as count FROM goals", conn).iloc[0]['count']
        st.metric("Total Goals", total_goals)

    st.markdown("---")

    # Display users table
    st.subheader("📋 Registered Users")

    if not users.empty:
        # Format the dataframe for display
        display_df = users.copy()
        display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": "User ID",
                "username": "Username",
                "email": "Email",
                "created_at": "Registered On"
            }
        )

        st.markdown("---")

        # User statistics
        st.subheader("📊 User Activity Statistics")

        user_stats = pd.read_sql_query("""
            SELECT
                u.username,
                COUNT(DISTINCT t.id) as total_tasks,
                COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks,
                COUNT(DISTINCT g.id) as total_goals,
                COUNT(DISTINCT de.id) as journal_entries
            FROM users u
            LEFT JOIN tasks t ON u.id = t.user_id
            LEFT JOIN goals g ON u.id = g.user_id
            LEFT JOIN daily_entries de ON u.id = de.user_id
            GROUP BY u.id, u.username
            ORDER BY total_tasks DESC
        """, conn)

        if not user_stats.empty:
            st.dataframe(
                user_stats,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "username": "Username",
                    "total_tasks": "Total Tasks",
                    "completed_tasks": "Completed Tasks",
                    "total_goals": "Goals",
                    "journal_entries": "Journal Entries"
                }
            )

        st.markdown("---")

        # Delete user section
        st.subheader("⚠️ Delete User")
        st.warning("Deleting a user will permanently remove all their data (tasks, goals, journal entries, achievements)")

        # Use a simpler approach without forms
        col1, col2 = st.columns(2)

        with col1:
            username_to_delete = st.selectbox(
                "Select user to delete",
                options=users['username'].tolist(),
                key="admin_delete_user_select"
            )

        with col2:
            confirm_text = st.text_input(
                "Type 'DELETE' to confirm",
                key="admin_delete_confirm",
                placeholder="DELETE"
            )

        if st.button("🗑️ Delete User", type="primary", key="admin_delete_button"):
            if confirm_text == "DELETE":
                # Use the SAME connection that's already open to avoid isolation issues
                # Re-query to get current user and verify they exist
                current_users = pd.read_sql_query(db.convert_sql("""
                    SELECT id, username FROM users WHERE username = ?
                """), conn, params=(username_to_delete,))

                if current_users.empty:
                    st.error(f"❌ User '{username_to_delete}' not found in database. They may have already been deleted.")
                    st.info("Please refresh the page to see the current user list.")
                else:
                    delete_user_id = current_users.iloc[0]['id']

                    # Prevent self-deletion
                    if delete_user_id == user_id:
                        st.error("❌ You cannot delete your own account while logged in! Please create another admin account or use a different account to delete this one.")
                    else:
                        try:
                            # Use the existing connection instead of creating a new one
                            delete_cursor = conn.cursor()

                            # Disable foreign keys
                            delete_cursor.execute("PRAGMA foreign_keys = OFF")

                            # Delete in correct order to avoid foreign key constraints
                            delete_cursor.execute(db.convert_sql("DELETE FROM achievements WHERE user_id = ?"), (delete_user_id,))
                            achievements_deleted = delete_cursor.rowcount

                            delete_cursor.execute(db.convert_sql("DELETE FROM daily_entries WHERE user_id = ?"), (delete_user_id,))
                            entries_deleted = delete_cursor.rowcount

                            delete_cursor.execute(db.convert_sql("DELETE FROM goals WHERE user_id = ?"), (delete_user_id,))
                            goals_deleted = delete_cursor.rowcount

                            delete_cursor.execute(db.convert_sql("DELETE FROM tasks WHERE user_id = ?"), (delete_user_id,))
                            tasks_deleted = delete_cursor.rowcount

                            delete_cursor.execute(db.convert_sql("DELETE FROM users WHERE id = ?"), (delete_user_id,))
                            user_deleted = delete_cursor.rowcount

                            conn.commit()

                            st.info(f"📊 Deletion results: {user_deleted} user, {tasks_deleted} tasks, {goals_deleted} goals, {entries_deleted} entries, {achievements_deleted} achievements")

                            if user_deleted > 0:
                                st.success(f"✅ Successfully deleted user '{username_to_delete}'!")
                                show_fireworks()
                                st.info("Refreshing page in 2 seconds...")
                                import time
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"❌ DELETE statement executed but returned 0 rows. This might be a database locking or permission issue.")

                        except Exception as e:
                            st.error(f"❌ Error deleting user: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
            elif confirm_text != "":
                st.error("❌ You must type 'DELETE' exactly (all caps) to confirm")
            else:
                st.warning("⚠️ Please type 'DELETE' to confirm deletion")
    else:
        st.info("No users registered yet!")

    # Close connection if it's still open
    try:
        conn.close()
    except:
        pass

    # Database info
    st.markdown("---")
    st.subheader("💾 Database Information")
    st.caption("Database: productivity_planner_multiuser.db")
    st.caption("⚠️ Note: Passwords are securely hashed with Argon2 and cannot be viewed")

def show_ai_assistant(user_id):
    st.header("🤖 AI Productivity Assistant")
    st.caption("Powered by Google Gemini")

    # Check if Gemini library is available
    if not GEMINI_AVAILABLE:
        st.error("⚠️ Google Generative AI library not installed")
        st.markdown("The app is redeploying. Please wait 2-3 minutes and refresh.")
        st.info("If this persists, check that `google-generativeai>=0.3.0` is in requirements.txt")
        return

    # Check if API key is configured
    has_key = False

    try:
        if hasattr(st, 'secrets') and "GOOGLE_API_KEY" in st.secrets:
            has_key = True
    except:
        pass

    if not has_key:
        st.error("⚠️ Google Gemini API Key Not Configured")
        st.markdown("""
        ## Quick Setup

        ### Step 1: Get Your API Key
        Visit [Google AI Studio](https://makersuite.google.com/app/apikey) and create an API key

        ### Step 2: Add to Secrets
        In your app settings → "Secrets", add:
        ```toml
        GOOGLE_API_KEY = "your-api-key-here"
        ```

        ### Step 3: Save and Refresh
        Your app will restart automatically and AI features will be ready!
        """)
        return

    # Show active status
    st.success("✅ AI Assistant is active and ready!")
    st.markdown("💬 **Create tasks with natural language, get productivity insights, and plan your day!**")
    st.markdown("---")

    # AI Feature Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat Assistant", "📝 Create Tasks", "💡 Get Insights", "📅 Plan Today"])

    with tab1:
        st.subheader("💬 Chat with Your AI Assistant")
        st.caption("Ask questions about productivity, get advice, or discuss your goals")

        # Chat interface
        user_question = st.text_area(
            "What would you like to ask?",
            placeholder="Example: How can I be more productive? What should I prioritize today? Give me tips for staying focused.",
            height=100,
            key="ai_chat_input"
        )

        if st.button("🤖 Ask AI", use_container_width=True, type="primary"):
            if user_question:
                with st.spinner("AI is thinking..."):
                    response = ai_chat_assistant(user_question, user_id)
                    st.markdown("### 🤖 AI Response:")
                    st.info(response)
            else:
                st.warning("Please enter a question first!")

        # Example questions
        st.markdown("---")
        st.caption("💡 **Example Questions:**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("How can I improve my productivity?", key="example1"):
                with st.spinner("AI is thinking..."):
                    response = ai_chat_assistant("How can I improve my productivity based on my current stats?", user_id)
                    st.markdown("### 🤖 AI Response:")
                    st.info(response)

        with col2:
            if st.button("What are my productivity strengths?", key="example2"):
                with st.spinner("AI is thinking..."):
                    response = ai_chat_assistant("Based on my productivity stats, what am I doing well?", user_id)
                    st.markdown("### 🤖 AI Response:")
                    st.info(response)

    with tab2:
        st.subheader("📝 Create Tasks with Natural Language")
        st.caption("Describe your tasks in plain English and let AI create them for you!")

        user_input = st.text_area(
            "Describe your tasks:",
            placeholder="Example: I need to prepare a presentation for Monday's meeting, call the dentist tomorrow, and finish the project report by Friday afternoon. Also schedule time to exercise 3 times this week.",
            height=120,
            key="ai_create_tasks_input"
        )

        if st.button("🪄 Create Tasks with AI", use_container_width=True, type="primary"):
            if user_input:
                with st.spinner("AI is creating your tasks..."):
                    num_tasks, message = ai_create_tasks(user_input, user_id)
                    if num_tasks > 0:
                        st.success(message)
                        show_fireworks()
                        st.markdown(f"**{num_tasks} task(s) have been added to your task list!**")
                        st.info("Go to the Tasks tab to view and manage them.")
                    else:
                        st.error(message)
            else:
                st.warning("Please describe the tasks you want to create!")

        # Example prompts
        st.markdown("---")
        st.caption("💡 **Example Prompts:**")
        st.markdown("""
        - "I need to organize a team meeting next week and prepare the quarterly report"
        - "Help me plan my workout routine: gym on Monday, Wednesday, Friday"
        - "Create tasks for my home renovation project: get quotes, buy materials, schedule contractor"
        - "I want to learn Python: find a course, practice daily, build a project"
        """)

    with tab3:
        st.subheader("💡 Productivity Insights")
        st.caption("Get AI-powered analysis of your productivity patterns")

        if st.button("📊 Analyze My Productivity", use_container_width=True, type="primary"):
            with st.spinner("Analyzing your productivity patterns..."):
                insights = ai_productivity_insights(user_id)
                st.markdown("### 💡 Your Productivity Insights:")
                st.info(insights)

        # Show quick stats
        st.markdown("---")
        st.caption("📈 **Current Stats:**")
        stats = get_productivity_stats(user_id)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tasks", stats['total_tasks'])
        with col2:
            st.metric("Completed", stats['completed_tasks'])
        with col3:
            st.metric("Completion Rate", f"{stats['completion_rate']:.0f}%")
        with col4:
            st.metric("Streak", f"{stats['streak']} days")

    with tab4:
        st.subheader("📅 AI Daily Planner")
        st.caption("Get AI suggestions for what to focus on today")

        if st.button("🎯 Generate Today's Plan", use_container_width=True, type="primary"):
            with st.spinner("Creating your optimal daily plan..."):
                plan = ai_daily_planner(user_id)
                st.markdown("### 📋 Today's Suggested Focus:")
                st.success(plan)

        # Show pending tasks count
        st.markdown("---")
        pending_tasks = get_tasks(user_id, status='pending')
        if not pending_tasks.empty:
            st.caption(f"📝 **You have {len(pending_tasks)} pending tasks**")

            # Quick preview of high priority tasks
            high_priority = pending_tasks[pending_tasks['priority'] == 'high']
            if not high_priority.empty:
                st.warning(f"⚠️ **{len(high_priority)} high priority tasks** need your attention!")

    # AI Features Overview
    st.markdown("---")
    st.subheader("🌟 AI Features Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **💬 Natural Language Task Creation**
        - Describe tasks in plain English
        - AI extracts title, category, priority
        - Automatically sets due dates
        - Estimates time required

        **📅 Smart Daily Planning**
        - Suggests optimal task order
        - Considers priorities and deadlines
        - Balances workload
        - Adapts to your patterns
        """)

    with col2:
        st.markdown("""
        **💡 Productivity Insights**
        - Analyzes completion patterns
        - Identifies productive times
        - Suggests improvements
        - Tracks progress trends

        **🤖 Intelligent Chat Assistant**
        - Answers productivity questions
        - Provides personalized advice
        - Helps with goal setting
        - Offers motivation and tips
        """)

if __name__ == "__main__":
    main()
