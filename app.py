import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Optional
import random
import json

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
    .stat-card {
        padding: 1.5rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
    .task-complete {
        color: #10b981;
        font-weight: bold;
    }
    .task-pending {
        color: #f59e0b;
        font-weight: bold;
    }
    .task-overdue {
        color: #ef4444;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Database initialization
class DatabaseManager:
    def __init__(self, db_name="productivity_planner.db"):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                priority TEXT,
                status TEXT DEFAULT 'pending',
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                estimated_hours REAL,
                tags TEXT
            )
        """)

        # Goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                target_date DATE,
                progress INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Daily entries table (for journaling and reflections)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date DATE UNIQUE,
                mood INTEGER,
                gratitude TEXT,
                highlights TEXT,
                challenges TEXT,
                tomorrow_goals TEXT
            )
        """)

        # Achievements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                icon TEXT
            )
        """)

        conn.commit()
        conn.close()

# Initialize database
db = DatabaseManager()

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
    "Great things never come from comfort zones.",
    "Success doesn't just find you. You have to go out and get it.",
    "The key to success is to focus on goals, not obstacles.",
    "Don't stop when you're tired. Stop when you're done.",
    "Your limitation—it's only your imagination."
]

def get_daily_quote():
    """Get a consistent daily quote based on the date"""
    random.seed(datetime.now().strftime("%Y-%m-%d"))
    return random.choice(MOTIVATIONAL_QUOTES)

# Task Management Functions
def add_task(title, description, category, priority, due_date, estimated_hours, tags):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (title, description, category, priority, due_date, estimated_hours, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, description, category, priority, due_date, estimated_hours, json.dumps(tags)))
    conn.commit()
    conn.close()
    check_achievements()

def get_tasks(status=None, category=None):
    conn = db.get_connection()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

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

def update_task_status(task_id, new_status):
    conn = db.get_connection()
    cursor = conn.cursor()

    if new_status == 'completed':
        cursor.execute("""
            UPDATE tasks SET status = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, task_id))
    else:
        cursor.execute("""
            UPDATE tasks SET status = ?
            WHERE id = ?
        """, (new_status, task_id))

    conn.commit()
    conn.close()
    check_achievements()

def delete_task(task_id):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# Goal Management Functions
def add_goal(title, description, target_date):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO goals (title, description, target_date)
        VALUES (?, ?, ?)
    """, (title, description, target_date))
    conn.commit()
    conn.close()

def get_goals(status='active'):
    conn = db.get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM goals WHERE status = ? ORDER BY target_date ASC",
        conn,
        params=(status,)
    )
    conn.close()
    return df

def update_goal_progress(goal_id, progress):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE goals SET progress = ?, status = ?
        WHERE id = ?
    """, (progress, 'completed' if progress >= 100 else 'active', goal_id))
    conn.commit()
    conn.close()
    check_achievements()

# Analytics Functions
def get_productivity_stats():
    conn = db.get_connection()

    # Total tasks
    total_tasks = pd.read_sql_query("SELECT COUNT(*) as count FROM tasks", conn).iloc[0]['count']

    # Completed tasks
    completed_tasks = pd.read_sql_query(
        "SELECT COUNT(*) as count FROM tasks WHERE status = 'completed'", conn
    ).iloc[0]['count']

    # Tasks completed this week
    week_completed = pd.read_sql_query("""
        SELECT COUNT(*) as count FROM tasks
        WHERE status = 'completed'
        AND completed_at >= date('now', '-7 days')
    """, conn).iloc[0]['count']

    # Current streak
    streak = calculate_streak()

    # Active goals
    active_goals = pd.read_sql_query(
        "SELECT COUNT(*) as count FROM goals WHERE status = 'active'", conn
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

def calculate_streak():
    """Calculate consecutive days with completed tasks"""
    conn = db.get_connection()
    df = pd.read_sql_query("""
        SELECT DATE(completed_at) as date FROM tasks
        WHERE status = 'completed'
        ORDER BY completed_at DESC
    """, conn)
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

# Achievement System
def check_achievements():
    """Check and award new achievements"""
    conn = db.get_connection()
    cursor = conn.cursor()

    stats = get_productivity_stats()

    achievements = [
        (5, "First Steps", "Completed 5 tasks", "🌱"),
        (25, "Getting Started", "Completed 25 tasks", "🚀"),
        (50, "Halfway Hero", "Completed 50 tasks", "⭐"),
        (100, "Century Club", "Completed 100 tasks", "💯"),
        (7, "Week Warrior", "7-day streak", "🔥"),
        (30, "Monthly Master", "30-day streak", "👑"),
    ]

    for threshold, name, description, icon in achievements:
        # Check if already earned
        existing = pd.read_sql_query(
            "SELECT * FROM achievements WHERE name = ?",
            conn,
            params=(name,)
        )

        if existing.empty:
            if threshold <= 50 and stats['completed_tasks'] >= threshold:
                cursor.execute("""
                    INSERT INTO achievements (name, description, icon)
                    VALUES (?, ?, ?)
                """, (name, description, icon))
            elif threshold > 50 and stats['streak'] >= threshold:
                cursor.execute("""
                    INSERT INTO achievements (name, description, icon)
                    VALUES (?, ?, ?)
                """, (name, description, icon))

    conn.commit()
    conn.close()

def get_achievements():
    conn = db.get_connection()
    df = pd.read_sql_query("SELECT * FROM achievements ORDER BY earned_at DESC", conn)
    conn.close()
    return df

# Daily Entry Functions
def save_daily_entry(entry_date, mood, gratitude, highlights, challenges, tomorrow_goals):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO daily_entries
        (entry_date, mood, gratitude, highlights, challenges, tomorrow_goals)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (entry_date, mood, gratitude, highlights, challenges, tomorrow_goals))
    conn.commit()
    conn.close()

def get_daily_entry(entry_date):
    conn = db.get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM daily_entries WHERE entry_date = ?",
        conn,
        params=(entry_date,)
    )
    conn.close()
    return df

# Main App
def main():
    st.markdown('<h1 class="main-header">🚀 Ultimate Productivity Planner</h1>', unsafe_allow_html=True)

    # Display daily motivational quote
    st.markdown(f'<div class="motivational-quote">💭 {get_daily_quote()}</div>', unsafe_allow_html=True)

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", [
        "📊 Dashboard",
        "✅ Tasks",
        "🎯 Goals",
        "📅 Calendar View",
        "📝 Daily Journal",
        "🏆 Achievements",
        "📈 Analytics"
    ])

    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "✅ Tasks":
        show_tasks()
    elif page == "🎯 Goals":
        show_goals()
    elif page == "📅 Calendar View":
        show_calendar()
    elif page == "📝 Daily Journal":
        show_daily_journal()
    elif page == "🏆 Achievements":
        show_achievements()
    elif page == "📈 Analytics":
        show_analytics()

def show_dashboard():
    st.header("📊 Your Productivity Dashboard")

    stats = get_productivity_stats()

    # Stats cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Tasks", stats['total_tasks'], delta=None)
        st.metric("Completed", stats['completed_tasks'])

    with col2:
        st.metric("This Week", stats['week_completed'])
        st.metric("Completion Rate", f"{stats['completion_rate']:.1f}%")

    with col3:
        st.metric("Current Streak", f"{stats['streak']} days", delta=None)
        st.metric("Active Goals", stats['active_goals'])

    with col4:
        # Show progress toward next achievement
        next_milestone = next((m for m in [5, 25, 50, 100] if m > stats['completed_tasks']), 100)
        remaining = next_milestone - stats['completed_tasks']
        st.metric("Next Milestone", f"{next_milestone} tasks")
        st.metric("Tasks to Go", remaining)

    st.markdown("---")

    # Today's tasks
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📋 Today's Tasks")
        today = datetime.now().strftime("%Y-%m-%d")
        today_tasks = get_tasks(status='pending')

        if not today_tasks.empty:
            today_tasks['due_date'] = pd.to_datetime(today_tasks['due_date'])
            urgent_tasks = today_tasks[today_tasks['due_date'] <= datetime.now().date()]

            if not urgent_tasks.empty:
                for _, task in urgent_tasks.head(5).iterrows():
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        priority_emoji = "🔴" if task['priority'] == 'high' else "🟡" if task['priority'] == 'medium' else "🟢"
                        st.write(f"{priority_emoji} **{task['title']}** - Due: {task['due_date'].strftime('%Y-%m-%d')}")
                    with col_b:
                        if st.button("✓", key=f"complete_dash_{task['id']}"):
                            update_task_status(task['id'], 'completed')
                            st.rerun()
            else:
                st.success("🎉 No urgent tasks! You're doing great!")
        else:
            st.info("No pending tasks. Time to add some goals!")

    with col2:
        st.subheader("🎯 Active Goals")
        goals = get_goals()

        if not goals.empty:
            for _, goal in goals.head(3).iterrows():
                st.write(f"**{goal['title']}**")
                st.progress(goal['progress'] / 100)
                st.caption(f"{goal['progress']}% complete")
        else:
            st.info("No active goals. Set some in the Goals section!")

def show_tasks():
    st.header("✅ Task Management")

    tab1, tab2 = st.tabs(["📝 Add Task", "📋 View Tasks"])

    with tab1:
        with st.form("add_task_form"):
            st.subheader("Create New Task")

            col1, col2 = st.columns(2)

            with col1:
                title = st.text_input("Task Title*", placeholder="Enter task title...")
                category = st.selectbox("Category", ["Work", "Personal", "Health", "Learning", "Finance", "Other"])
                priority = st.selectbox("Priority", ["high", "medium", "low"])

            with col2:
                due_date = st.date_input("Due Date", value=datetime.now() + timedelta(days=1))
                estimated_hours = st.number_input("Estimated Hours", min_value=0.0, max_value=100.0, value=1.0, step=0.5)
                tags_input = st.text_input("Tags (comma-separated)", placeholder="urgent, important, meeting")

            description = st.text_area("Description", placeholder="Add details about this task...")

            submitted = st.form_submit_button("➕ Add Task", use_container_width=True)

            if submitted and title:
                tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
                add_task(title, description, category, priority, due_date.strftime("%Y-%m-%d"), estimated_hours, tags)
                st.success(f"✅ Task '{title}' added successfully!")
                st.rerun()
            elif submitted:
                st.error("Please enter a task title!")

    with tab2:
        st.subheader("Your Tasks")

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox("Filter by Status", ["all", "pending", "in_progress", "completed"])

        with col2:
            category_filter = st.selectbox("Filter by Category", ["all", "Work", "Personal", "Health", "Learning", "Finance", "Other"])

        with col3:
            sort_by = st.selectbox("Sort by", ["Due Date", "Priority", "Created Date"])

        # Get tasks
        tasks = get_tasks(
            status=None if status_filter == "all" else status_filter,
            category=None if category_filter == "all" else category_filter
        )

        if not tasks.empty:
            tasks['due_date'] = pd.to_datetime(tasks['due_date'])

            # Display tasks
            for _, task in tasks.iterrows():
                with st.expander(f"{task['title']} - {task['category']} ({task['priority']} priority)"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"**Description:** {task['description']}")
                        st.write(f"**Due Date:** {task['due_date'].strftime('%Y-%m-%d')}")
                        st.write(f"**Status:** {task['status']}")
                        st.write(f"**Estimated Hours:** {task['estimated_hours']}")
                        if task['tags']:
                            tags = json.loads(task['tags'])
                            st.write(f"**Tags:** {', '.join(tags)}")

                    with col2:
                        if task['status'] != 'completed':
                            if st.button("✓ Complete", key=f"complete_{task['id']}"):
                                update_task_status(task['id'], 'completed')
                                st.success("Task completed!")
                                st.rerun()

                            if st.button("🔄 In Progress", key=f"progress_{task['id']}"):
                                update_task_status(task['id'], 'in_progress')
                                st.rerun()

                        if st.button("🗑️ Delete", key=f"delete_{task['id']}"):
                            delete_task(task['id'])
                            st.rerun()
        else:
            st.info("No tasks found. Add your first task above!")

def show_goals():
    st.header("🎯 Goal Tracking")

    tab1, tab2 = st.tabs(["➕ Add Goal", "📊 View Goals"])

    with tab1:
        with st.form("add_goal_form"):
            st.subheader("Set a New Goal")

            title = st.text_input("Goal Title*", placeholder="What do you want to achieve?")
            description = st.text_area("Description", placeholder="Describe your goal in detail...")
            target_date = st.date_input("Target Date", value=datetime.now() + timedelta(days=30))

            submitted = st.form_submit_button("🎯 Add Goal", use_container_width=True)

            if submitted and title:
                add_goal(title, description, target_date.strftime("%Y-%m-%d"))
                st.success(f"🎯 Goal '{title}' created!")
                st.rerun()
            elif submitted:
                st.error("Please enter a goal title!")

    with tab2:
        st.subheader("Your Goals")

        goals = get_goals()

        if not goals.empty:
            for _, goal in goals.iterrows():
                with st.expander(f"{goal['title']} - {goal['progress']}% Complete"):
                    st.write(f"**Description:** {goal['description']}")
                    st.write(f"**Target Date:** {goal['target_date']}")
                    st.write(f"**Status:** {goal['status']}")

                    # Progress slider
                    new_progress = st.slider(
                        "Update Progress",
                        0, 100,
                        int(goal['progress']),
                        key=f"progress_slider_{goal['id']}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("💾 Update Progress", key=f"update_{goal['id']}"):
                            update_goal_progress(goal['id'], new_progress)
                            st.success("Progress updated!")
                            st.rerun()

                    with col2:
                        if new_progress == 100:
                            st.balloons()
                            st.success("🎉 Goal Completed! Amazing work!")
        else:
            st.info("No goals yet. Set your first goal above!")

def show_calendar():
    st.header("📅 Calendar View")

    # Get all tasks
    tasks = get_tasks()

    if not tasks.empty:
        tasks['due_date'] = pd.to_datetime(tasks['due_date'])

        # Create a calendar view using plotly
        fig = px.timeline(
            tasks,
            x_start="created_at",
            x_end="due_date",
            y="title",
            color="priority",
            color_discrete_map={"high": "#ef4444", "medium": "#f59e0b", "low": "#10b981"},
            title="Task Timeline"
        )

        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig, use_container_width=True)

        # Week view
        st.subheader("📆 This Week's Schedule")

        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        week_end = week_start + timedelta(days=7)

        week_tasks = tasks[(tasks['due_date'] >= week_start) & (tasks['due_date'] < week_end)]

        if not week_tasks.empty:
            for day_offset in range(7):
                current_day = week_start + timedelta(days=day_offset)
                day_name = current_day.strftime("%A, %B %d")

                day_tasks = week_tasks[week_tasks['due_date'].dt.date == current_day.date()]

                if not day_tasks.empty:
                    st.markdown(f"**{day_name}**")
                    for _, task in day_tasks.iterrows():
                        priority_emoji = "🔴" if task['priority'] == 'high' else "🟡" if task['priority'] == 'medium' else "🟢"
                        status_emoji = "✅" if task['status'] == 'completed' else "⏳"
                        st.write(f"{status_emoji} {priority_emoji} {task['title']} ({task['category']})")
        else:
            st.info("No tasks scheduled for this week!")
    else:
        st.info("No tasks to display on calendar. Add some tasks first!")

def show_daily_journal():
    st.header("📝 Daily Journal & Reflection")

    entry_date = st.date_input("Select Date", value=datetime.now())
    entry_date_str = entry_date.strftime("%Y-%m-%d")

    # Check if entry exists
    existing_entry = get_daily_entry(entry_date_str)

    with st.form("daily_journal_form"):
        st.subheader(f"Journal Entry for {entry_date.strftime('%B %d, %Y')}")

        # Mood tracker
        mood = st.slider("How are you feeling today? (1-10)", 1, 10,
                        value=int(existing_entry.iloc[0]['mood']) if not existing_entry.empty and existing_entry.iloc[0]['mood'] else 7)

        # Gratitude
        gratitude = st.text_area("🙏 What are you grateful for today?",
                                value=existing_entry.iloc[0]['gratitude'] if not existing_entry.empty else "",
                                placeholder="List 3 things you're grateful for...")

        # Highlights
        highlights = st.text_area("✨ Today's Highlights",
                                 value=existing_entry.iloc[0]['highlights'] if not existing_entry.empty else "",
                                 placeholder="What went well today?")

        # Challenges
        challenges = st.text_area("💪 Challenges & Learnings",
                                 value=existing_entry.iloc[0]['challenges'] if not existing_entry.empty else "",
                                 placeholder="What challenged you? What did you learn?")

        # Tomorrow's goals
        tomorrow_goals = st.text_area("🎯 Tomorrow's Top 3 Goals",
                                     value=existing_entry.iloc[0]['tomorrow_goals'] if not existing_entry.empty else "",
                                     placeholder="What are your top 3 priorities for tomorrow?")

        submitted = st.form_submit_button("💾 Save Entry", use_container_width=True)

        if submitted:
            save_daily_entry(entry_date_str, mood, gratitude, highlights, challenges, tomorrow_goals)
            st.success("✅ Journal entry saved!")
            st.balloons()

    # Show mood history
    st.markdown("---")
    st.subheader("📊 Mood Tracker History")

    conn = db.get_connection()
    mood_history = pd.read_sql_query(
        "SELECT entry_date, mood FROM daily_entries ORDER BY entry_date DESC LIMIT 30",
        conn
    )
    conn.close()

    if not mood_history.empty:
        fig = px.line(mood_history, x='entry_date', y='mood',
                     title='Your Mood Over Time',
                     labels={'entry_date': 'Date', 'mood': 'Mood (1-10)'},
                     markers=True)
        fig.update_layout(yaxis_range=[0, 10])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Start journaling to see your mood trends!")

def show_achievements():
    st.header("🏆 Achievements & Milestones")

    achievements = get_achievements()
    stats = get_productivity_stats()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🎖️ Earned Achievements")

        if not achievements.empty:
            for _, achievement in achievements.iterrows():
                st.markdown(f"""
                <div class="achievement-badge">
                    {achievement['icon']} {achievement['name']} - {achievement['description']}
                </div>
                """, unsafe_allow_html=True)
                st.caption(f"Earned on {achievement['earned_at']}")
        else:
            st.info("Complete tasks to earn achievements!")

    with col2:
        st.subheader("📈 Progress to Next Achievement")

        milestones = [
            (5, "First Steps", "🌱"),
            (25, "Getting Started", "🚀"),
            (50, "Halfway Hero", "⭐"),
            (100, "Century Club", "💯"),
        ]

        completed = stats['completed_tasks']

        for threshold, name, icon in milestones:
            if completed >= threshold:
                st.success(f"{icon} {name} - Unlocked!")
            else:
                remaining = threshold - completed
                progress = (completed / threshold) * 100
                st.write(f"{icon} {name}")
                st.progress(progress / 100)
                st.caption(f"{remaining} tasks to go")

        st.markdown("---")
        st.subheader("🔥 Streak Achievement")

        streak = stats['streak']

        if streak >= 30:
            st.success("👑 Monthly Master - 30 day streak!")
        elif streak >= 7:
            st.success("🔥 Week Warrior - 7 day streak!")
        else:
            remaining = 7 - streak
            st.write(f"Current streak: {streak} days")
            st.progress(streak / 7)
            st.caption(f"{remaining} days to Week Warrior!")

def show_analytics():
    st.header("📈 Productivity Analytics")

    conn = db.get_connection()

    # Task completion over time
    st.subheader("📊 Task Completion Trend")

    completion_data = pd.read_sql_query("""
        SELECT DATE(completed_at) as date, COUNT(*) as count
        FROM tasks
        WHERE status = 'completed' AND completed_at IS NOT NULL
        GROUP BY DATE(completed_at)
        ORDER BY date DESC
        LIMIT 30
    """, conn)

    if not completion_data.empty:
        fig = px.bar(completion_data, x='date', y='count',
                    title='Tasks Completed per Day (Last 30 Days)',
                    labels={'date': 'Date', 'count': 'Tasks Completed'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Complete some tasks to see trends!")

    # Category breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Tasks by Category")

        category_data = pd.read_sql_query("""
            SELECT category, COUNT(*) as count
            FROM tasks
            GROUP BY category
        """, conn)

        if not category_data.empty:
            fig = px.pie(category_data, values='count', names='category',
                        title='Task Distribution by Category')
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🎯 Tasks by Priority")

        priority_data = pd.read_sql_query("""
            SELECT priority, COUNT(*) as count
            FROM tasks
            GROUP BY priority
        """, conn)

        if not priority_data.empty:
            fig = px.pie(priority_data, values='count', names='priority',
                        title='Task Distribution by Priority',
                        color='priority',
                        color_discrete_map={'high': '#ef4444', 'medium': '#f59e0b', 'low': '#10b981'})
            st.plotly_chart(fig, use_container_width=True)

    # Productivity insights
    st.subheader("💡 Productivity Insights")

    stats = get_productivity_stats()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Average Daily Completion", f"{stats['week_completed'] / 7:.1f}", delta=None)

    with col2:
        st.metric("Task Completion Rate", f"{stats['completion_rate']:.1f}%")

    with col3:
        # Calculate estimated hours
        total_hours = pd.read_sql_query(
            "SELECT SUM(estimated_hours) as total FROM tasks WHERE status = 'completed'",
            conn
        ).iloc[0]['total']
        st.metric("Total Hours Invested", f"{total_hours:.1f}h" if total_hours else "0h")

    conn.close()

    # Motivational message based on performance
    st.markdown("---")

    if stats['completion_rate'] >= 80:
        st.success("🌟 Outstanding! You're crushing your goals! Keep up the amazing work!")
    elif stats['completion_rate'] >= 60:
        st.info("💪 Great progress! You're building solid momentum!")
    elif stats['completion_rate'] >= 40:
        st.warning("📈 Good start! Keep pushing forward, you've got this!")
    else:
        st.info("🚀 Every journey starts with a single step. You can do this!")

if __name__ == "__main__":
    main()
