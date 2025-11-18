# 🤖 AI Integration Guide for Productivity Planner

## Overview
This guide explains how to add AI capabilities to your productivity planner using natural language processing to create tasks, analyze productivity, and provide intelligent suggestions.

---

## Part 1: Task Completion Celebrations & Editing ✅

### Already Implemented:
- **Celebrations on Task Completion**: 🎈 Balloons + ❄️ Snow animations
- **Task Editing**: Click "✏️ Edit" button to modify any task field
- **Success Messages**: Clear feedback for all actions

---

## Part 2: AI Integration Options

### Option 1: OpenAI GPT Integration (Recommended)

**Features:**
- Natural language task creation
- Intelligent task prioritization
- Daily task suggestions based on patterns
- Productivity insights and recommendations

**Setup Steps:**

1. **Install Required Packages:**
```bash
pip install openai
```

2. **Update requirements.txt:**
```
streamlit>=1.31.0
pandas>=2.0.0
plotly>=5.18.0
argon2-cffi>=23.1.0
openai>=1.0.0
```

3. **Add Streamlit Secrets** (for API key):
- Create `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "your-api-key-here"
```

4. **Implementation Example:**

```python
import openai
import json

# Initialize OpenAI
openai.api_key = st.secrets["OPENAI_API_KEY"]

def ai_create_tasks(user_prompt, user_id):
    """Use AI to create tasks from natural language"""

    system_prompt = """You are a productivity assistant. Convert user requests into structured tasks.
    Return a JSON array of tasks with these fields:
    - title: Task title (required)
    - description: Detailed description
    - category: One of [Work, Personal, Health, Learning, Finance, Other]
    - priority: One of [high, medium, low]
    - due_date: YYYY-MM-DD format
    - estimated_hours: Float number

    Example user input: "I need to finish my project report by Friday and schedule a dentist appointment"
    Example output: [
        {
            "title": "Finish project report",
            "description": "Complete and submit project report",
            "category": "Work",
            "priority": "high",
            "due_date": "2025-01-17",
            "estimated_hours": 3.0
        },
        {
            "title": "Schedule dentist appointment",
            "description": "Call dentist office to schedule appointment",
            "category": "Health",
            "priority": "medium",
            "due_date": "2025-01-20",
            "estimated_hours": 0.5
        }
    ]
    """

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    tasks_data = json.loads(response.choices[0].message.content)

    # Add tasks to database
    for task in tasks_data.get("tasks", []):
        add_task(
            user_id,
            task["title"],
            task.get("description", ""),
            task.get("category", "Other"),
            task.get("priority", "medium"),
            task.get("due_date", (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")),
            task.get("estimated_hours", 1.0),
            []
        )

    return len(tasks_data.get("tasks", []))

def ai_productivity_insights(user_id):
    """Generate AI insights about productivity patterns"""

    # Get user's task history
    conn = db.get_connection()
    tasks = pd.read_sql_query("""
        SELECT title, category, priority, status,
               DATE(created_at) as created, DATE(completed_at) as completed
        FROM tasks
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    """, conn, params=(user_id,))
    conn.close()

    if tasks.empty:
        return "Not enough data yet. Complete more tasks to get insights!"

    # Create context for AI
    task_summary = f"""
    User has {len(tasks)} recent tasks:
    - Completed: {len(tasks[tasks['status'] == 'completed'])}
    - Pending: {len(tasks[tasks['status'] == 'pending'])}
    - Categories: {tasks['category'].value_counts().to_dict()}
    - Priorities: {tasks['priority'].value_counts().to_dict()}
    """

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a productivity coach. Analyze task patterns and provide 3-4 actionable insights."},
            {"role": "user", "content": task_summary}
        ],
        temperature=0.7,
        max_tokens=300
    )

    return response.choices[0].message.content

def ai_daily_planner(user_id):
    """AI suggests tasks for today based on patterns"""

    # Get pending tasks and user patterns
    conn = db.get_connection()
    pending_tasks = pd.read_sql_query("""
        SELECT title, category, priority, due_date, estimated_hours
        FROM tasks
        WHERE user_id = ? AND status = 'pending'
        ORDER BY priority DESC, due_date ASC
    """, conn, params=(user_id,))
    conn.close()

    if pending_tasks.empty:
        return "You have no pending tasks! Great job! 🎉"

    context = f"User has {len(pending_tasks)} pending tasks. Suggest which 5-7 tasks to focus on today for optimal productivity."

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a productivity planner. Suggest a daily task list."},
            {"role": "user", "content": context + "\\n\\n" + pending_tasks.to_string()}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content
```

5. **Add AI Chat Tab to Dashboard:**

```python
def show_ai_assistant(user_id):
    st.header("🤖 AI Productivity Assistant")

    # AI Chat Interface
    st.subheader("💬 Chat with Your AI Assistant")

    user_input = st.text_area(
        "What would you like help with?",
        placeholder="Example: Create tasks for my project deadline next Friday, or suggest what I should work on today",
        height=100
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📝 Create Tasks", use_container_width=True):
            if user_input:
                with st.spinner("AI is creating tasks..."):
                    num_tasks = ai_create_tasks(user_input, user_id)
                    st.success(f"✅ Created {num_tasks} tasks!")
                    st.balloons()
            else:
                st.warning("Please describe what tasks you need")

    with col2:
        if st.button("💡 Get Insights", use_container_width=True):
            with st.spinner("Analyzing your productivity..."):
                insights = ai_productivity_insights(user_id)
                st.info(insights)

    with col3:
        if st.button("📅 Plan Today", use_container_width=True):
            with st.spinner("Creating your daily plan..."):
                plan = ai_daily_planner(user_id)
                st.success("📋 Today's Suggested Focus:")
                st.markdown(plan)

    # AI Features Overview
    st.markdown("---")
    st.subheader("🌟 AI Features")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Natural Language Task Creation**
        - Describe tasks in plain English
        - AI extracts title, category, priority
        - Automatically sets due dates

        **Smart Daily Planning**
        - Suggests optimal task order
        - Considers priorities and deadlines
        - Balances workload
        """)

    with col2:
        st.markdown("""
        **Productivity Insights**
        - Analyzes completion patterns
        - Identifies productive times
        - Suggests improvements

        **Intelligent Categorization**
        - Auto-categorizes tasks
        - Detects priority levels
        - Estimates time required
        """)
```

---

### Option 2: Google Gemini (Free Alternative)

**Setup:**
```bash
pip install google-generativeai
```

**Implementation:**
```python
import google.generativeai as genai

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-pro')

def ai_create_tasks_gemini(user_prompt, user_id):
    prompt = f"""Convert this request into structured tasks (JSON format):
    {user_prompt}

    Return JSON with 'tasks' array containing: title, description, category, priority, due_date, estimated_hours"""

    response = model.generate_content(prompt)
    # Parse and create tasks...
```

---

### Option 3: Local AI with Ollama (Free, Private)

**Setup:**
1. Install Ollama: https://ollama.ai
2. Run: `ollama pull llama2`
3. Install Python client: `pip install ollama`

**Implementation:**
```python
import ollama

def ai_create_tasks_local(user_prompt, user_id):
    response = ollama.chat(model='llama2', messages=[
        {'role': 'system', 'content': 'You are a productivity assistant...'},
        {'role': 'user', 'content': user_prompt}
    ])
    # Parse response and create tasks...
```

---

## Part 3: Adding AI Assistant Tab

Add this to your navigation in `main()`:

```python
# Update navigation options
nav_options = [
    "📊 Dashboard",
    "✅ Tasks",
    "🎯 Goals",
    "📅 Calendar View",
    "📝 Daily Journal",
    "🏆 Achievements",
    "📈 Analytics",
    "🤖 AI Assistant"  # NEW!
]

# Add in the page routing
elif page == "🤖 AI Assistant":
    show_ai_assistant(user_id)
```

---

## Part 4: Cost Considerations

### OpenAI GPT-4:
- **Cost**: ~$0.03 per 1K tokens (input), ~$0.06 per 1K tokens (output)
- **Typical task creation**: $0.01-0.02 per request
- **Monthly estimate**: $5-20 for regular use

### Google Gemini:
- **Free tier**: 60 requests/minute
- **Cost**: Much cheaper than GPT-4

### Ollama (Local):
- **Cost**: FREE (runs on your machine)
- **Privacy**: All data stays local
- **Speed**: Slower, requires good hardware

---

## Part 5: Advanced Features You Can Add

1. **Voice Input**: Use Whisper API for voice-to-task
2. **Task Suggestions**: AI recommends tasks based on goals
3. **Smart Scheduling**: AI optimizes task order
4. **Email Parsing**: Forward emails to create tasks
5. **Habit Analysis**: AI identifies productivity patterns
6. **Goal Recommendations**: AI suggests realistic goals
7. **Motivation Messages**: Personalized encouragement
8. **Weekly Reviews**: AI-generated productivity reports

---

## Next Steps

1. Choose an AI provider (OpenAI recommended for best results)
2. Get API key from provider
3. Add secrets to Streamlit
4. Implement the AI assistant functions
5. Add AI Assistant tab to navigation
6. Test with natural language task creation
7. Deploy to Streamlit Cloud with secrets configured

Would you like me to implement the full AI assistant for you? Let me know which option you prefer!
