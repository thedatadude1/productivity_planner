import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Optional
import random
import json
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

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
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                icon TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Migrate existing databases: add is_admin column if it doesn't exist
        try:
            cursor.execute("SELECT is_admin FROM users LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
            # Create admin account if username 'thedatadude' exists
            cursor.execute("SELECT id FROM users WHERE username = 'thedatadude'")
            admin_user = cursor.fetchone()
            if admin_user:
                cursor.execute("UPDATE users SET is_admin = 1 WHERE username = 'thedatadude'")

        conn.commit()
        conn.close()

# Initialize database
db = DatabaseManager()

# Initialize Argon2 password hasher
ph = PasswordHasher()

# Authentication Functions
def register_user(username, password, email=""):
    """Register a new user with Argon2 password hashing"""
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        # Hash password using Argon2
        password_hash = ph.hash(password)
        cursor.execute("""
            INSERT INTO users (username, password_hash, email)
            VALUES (?, ?, ?)
        """, (username, password_hash, email))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def login_user(username, password):
    """Login user with Argon2 password verification"""
    conn = db.get_connection()

    # Get user by username
    user = pd.read_sql_query("""
        SELECT id, username, password_hash, is_admin FROM users
        WHERE username = ?
    """, conn, params=(username,))
    conn.close()

    if not user.empty:
        try:
            # Verify password using Argon2
            ph.verify(user.iloc[0]['password_hash'], password)
            return user.iloc[0]['id'], user.iloc[0]['username'], bool(user.iloc[0]['is_admin'])
        except VerifyMismatchError:
            # Wrong password
            return None, None, False
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
    cursor.execute("""
        INSERT INTO tasks (user_id, title, description, category, priority, due_date, estimated_hours, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, title, description, category, priority, due_date, estimated_hours, json.dumps(tags)))
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

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def update_task_status(user_id, task_id, new_status):
    conn = db.get_connection()
    cursor = conn.cursor()

    if new_status == 'completed':
        cursor.execute("""
            UPDATE tasks SET status = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """, (new_status, task_id, user_id))
    else:
        cursor.execute("""
            UPDATE tasks SET status = ?
            WHERE id = ? AND user_id = ?
        """, (new_status, task_id, user_id))

    conn.commit()
    conn.close()
    check_achievements(user_id)

def delete_task(user_id, task_id):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    conn.close()

# Goal Management Functions (now user-specific)
def add_goal(user_id, title, description, target_date):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO goals (user_id, title, description, target_date)
        VALUES (?, ?, ?, ?)
    """, (user_id, title, description, target_date))
    conn.commit()
    conn.close()

def get_goals(user_id, status='active'):
    conn = db.get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM goals WHERE user_id = ? AND status = ? ORDER BY target_date ASC",
        conn,
        params=(user_id, status)
    )
    conn.close()
    return df

def update_goal_progress(user_id, goal_id, progress):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE goals SET progress = ?, status = ?
        WHERE id = ? AND user_id = ?
    """, (progress, 'completed' if progress >= 100 else 'active', goal_id, user_id))
    conn.commit()
    conn.close()
    check_achievements(user_id)

# Analytics Functions (now user-specific)
def get_productivity_stats(user_id):
    conn = db.get_connection()

    total_tasks = pd.read_sql_query(
        "SELECT COUNT(*) as count FROM tasks WHERE user_id = ?",
        conn, params=(user_id,)
    ).iloc[0]['count']

    completed_tasks = pd.read_sql_query(
        "SELECT COUNT(*) as count FROM tasks WHERE user_id = ? AND status = 'completed'",
        conn, params=(user_id,)
    ).iloc[0]['count']

    week_completed = pd.read_sql_query("""
        SELECT COUNT(*) as count FROM tasks
        WHERE user_id = ? AND status = 'completed'
        AND completed_at >= date('now', '-7 days')
    """, conn, params=(user_id,)).iloc[0]['count']

    streak = calculate_streak(user_id)

    active_goals = pd.read_sql_query(
        "SELECT COUNT(*) as count FROM goals WHERE user_id = ? AND status = 'active'",
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
    df = pd.read_sql_query("""
        SELECT DATE(completed_at) as date FROM tasks
        WHERE user_id = ? AND status = 'completed'
        ORDER BY completed_at DESC
    """, conn, params=(user_id,))
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
            "SELECT * FROM achievements WHERE user_id = ? AND name = ?",
            conn,
            params=(user_id, name)
        )

        if existing.empty:
            if threshold <= 50 and stats['completed_tasks'] >= threshold:
                cursor.execute("""
                    INSERT INTO achievements (user_id, name, description, icon)
                    VALUES (?, ?, ?, ?)
                """, (user_id, name, description, icon))
            elif threshold > 50 and stats['streak'] >= threshold:
                cursor.execute("""
                    INSERT INTO achievements (user_id, name, description, icon)
                    VALUES (?, ?, ?, ?)
                """, (user_id, name, description, icon))

    conn.commit()
    conn.close()

def get_achievements(user_id):
    conn = db.get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM achievements WHERE user_id = ? ORDER BY earned_at DESC",
        conn, params=(user_id,)
    )
    conn.close()
    return df

# Daily Entry Functions (now user-specific)
def save_daily_entry(user_id, entry_date, mood, gratitude, highlights, challenges, tomorrow_goals):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO daily_entries
        (user_id, entry_date, mood, gratitude, highlights, challenges, tomorrow_goals)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, entry_date, mood, gratitude, highlights, challenges, tomorrow_goals))
    conn.commit()
    conn.close()

def get_daily_entry(user_id, entry_date):
    conn = db.get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM daily_entries WHERE user_id = ? AND entry_date = ?",
        conn,
        params=(user_id, entry_date)
    )
    conn.close()
    return df

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
            submit = st.form_submit_button("Login")

            if submit:
                user_id, username_result, is_admin = login_user(username, password)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.username = username_result
                    st.session_state.user_id = user_id
                    st.session_state.is_admin = is_admin
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
        "📈 Analytics"
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
    elif page == "👥 Admin Panel":
        show_admin_panel(user_id)

# All the show_* functions remain the same but now accept user_id parameter
# I'll include the key ones here:

def show_dashboard(user_id):
    st.header("📊 Your Productivity Dashboard")
    stats = get_productivity_stats(user_id)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tasks", stats['total_tasks'])
        st.metric("Completed", stats['completed_tasks'])
    with col2:
        st.metric("This Week", stats['week_completed'])
        st.metric("Completion Rate", f"{stats['completion_rate']:.1f}%")
    with col3:
        st.metric("Current Streak", f"{stats['streak']} days")
        st.metric("Active Goals", stats['active_goals'])
    with col4:
        next_milestone = next((m for m in [5, 25, 50, 100] if m > stats['completed_tasks']), 100)
        remaining = next_milestone - stats['completed_tasks']
        st.metric("Next Milestone", f"{next_milestone} tasks")
        st.metric("Tasks to Go", remaining)

    st.markdown("---")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📋 Today's Tasks")
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

def show_tasks(user_id):
    st.header("✅ Task Management")
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
                st.success(f"✅ Task '{title}' added successfully!")
                st.rerun()

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
                                st.rerun()
                        if st.button("🗑️ Delete", key=f"delete_{task['id']}"):
                            delete_task(user_id, task['id'])
                            st.rerun()
        else:
            st.info("No tasks found. Add your first task above!")

def show_goals(user_id):
    st.header("🎯 Goal Tracking")
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
    entry_date = st.date_input("Select Date", value=datetime.now())
    entry_date_str = entry_date.strftime("%Y-%m-%d")
    existing_entry = get_daily_entry(user_id, entry_date_str)

    with st.form("daily_journal_form"):
        mood = st.slider("Mood (1-10)", 1, 10, value=int(existing_entry.iloc[0]['mood']) if not existing_entry.empty else 7)
        gratitude = st.text_area("🙏 Gratitude", value=existing_entry.iloc[0]['gratitude'] if not existing_entry.empty else "")
        highlights = st.text_area("✨ Highlights", value=existing_entry.iloc[0]['highlights'] if not existing_entry.empty else "")
        challenges = st.text_area("💪 Challenges", value=existing_entry.iloc[0]['challenges'] if not existing_entry.empty else "")
        tomorrow_goals = st.text_area("🎯 Tomorrow's Goals", value=existing_entry.iloc[0]['tomorrow_goals'] if not existing_entry.empty else "")
        submitted = st.form_submit_button("💾 Save Entry", use_container_width=True)

        if submitted:
            save_daily_entry(user_id, entry_date_str, mood, gratitude, highlights, challenges, tomorrow_goals)
            st.success("✅ Journal entry saved!")

def show_achievements_page(user_id):
    st.header("🏆 Achievements & Milestones")
    achievements = get_achievements(user_id)

    if not achievements.empty:
        for _, achievement in achievements.iterrows():
            st.markdown(f'<div class="achievement-badge">{achievement["icon"]} {achievement["name"]} - {achievement["description"]}</div>', unsafe_allow_html=True)
    else:
        st.info("Complete tasks to earn achievements!")

def show_analytics(user_id):
    st.header("📈 Productivity Analytics")
    stats = get_productivity_stats(user_id)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Daily Completion", f"{stats['week_completed'] / 7:.1f}")
    with col2:
        st.metric("Task Completion Rate", f"{stats['completion_rate']:.1f}%")
    with col3:
        st.metric("Current Streak", f"{stats['streak']} days")

    if stats['completion_rate'] >= 80:
        st.success("🌟 Outstanding! You're crushing your goals!")
    elif stats['completion_rate'] >= 60:
        st.info("💪 Great progress! Keep it up!")
    else:
        st.info("🚀 Every journey starts with a single step!")

def show_admin_panel(user_id):
    st.header("👥 Admin Panel - User Management")

    # Check if user is admin
    if not st.session_state.is_admin:
        st.error("🚫 Access Denied: Admin privileges required")
        st.warning("This page is only accessible to administrators.")
        return

    st.info("📊 View all registered users and database statistics")

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

        with st.form("delete_user_form"):
            username_to_delete = st.selectbox(
                "Select user to delete",
                options=users['username'].tolist(),
                key="delete_user_select"
            )

            confirm_text = st.text_input(
                "Type 'DELETE' to confirm",
                key="delete_confirm"
            )

            submitted = st.form_submit_button("🗑️ Delete User", type="primary")

            if submitted:
                if confirm_text == "DELETE":
                    # Get user_id
                    user_to_delete = users[users['username'] == username_to_delete].iloc[0]
                    delete_user_id = user_to_delete['id']

                    # Prevent self-deletion
                    if delete_user_id == user_id:
                        st.error("❌ You cannot delete your own account while logged in! Please create another admin account or use a different account to delete this one.")
                    else:
                        # Close the current connection and create a new one for deletion
                        conn.close()
                        delete_conn = db.get_connection()
                        cursor = delete_conn.cursor()

                        try:
                            # Delete in correct order to avoid foreign key constraints
                            cursor.execute("DELETE FROM achievements WHERE user_id = ?", (delete_user_id,))
                            cursor.execute("DELETE FROM daily_entries WHERE user_id = ?", (delete_user_id,))
                            cursor.execute("DELETE FROM goals WHERE user_id = ?", (delete_user_id,))
                            cursor.execute("DELETE FROM tasks WHERE user_id = ?", (delete_user_id,))
                            cursor.execute("DELETE FROM users WHERE id = ?", (delete_user_id,))
                            delete_conn.commit()
                            delete_conn.close()
                            st.success(f"✅ User '{username_to_delete}' and all associated data have been deleted!")
                            st.balloons()
                            st.info("Refreshing page in 2 seconds...")
                            import time
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            delete_conn.rollback()
                            delete_conn.close()
                            st.error(f"❌ Error deleting user: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
                elif confirm_text != "":
                    st.error("❌ You must type 'DELETE' exactly (all caps) to confirm")
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

if __name__ == "__main__":
    main()
