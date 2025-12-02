# 🆓 FREE AI Setup Guide

Your productivity planner now supports **completely FREE AI** features!

## Quick Start (5 minutes)

### Option 1: Google Gemini (EASIEST & FREE!)

1. **Get your FREE API key**:
   - Visit: https://makersuite.google.com/app/apikey
   - Click "Create API Key"
   - Copy the key (starts with `AIza...`)

2. **Add to your app**:
   - Create file: `.streamlit/secrets.toml`
   - Add this line:
   ```toml
   GOOGLE_API_KEY = "AIza-your-key-here"
   ```

3. **Run the app**:
   ```bash
   streamlit run app_multiuser.py
   ```

4. **Done!** Go to "🤖 AI Assistant" tab and start creating tasks with natural language!

### Option 2: Ollama (Local & Private - NO API KEY!)

1. **Install Ollama**:
   - Visit: https://ollama.ai
   - Download and install for your OS

2. **Download AI model**:
   ```bash
   ollama pull llama2
   ```

3. **Run the app**:
   ```bash
   streamlit run app_multiuser.py
   ```

4. **Done!** Ollama runs automatically in the background

## Fixing Data Loss Issue

If your tasks keep disappearing, here's the fix:

### Step 1: Initialize Database
```bash
python init_database.py
```

### Step 2: Create Admin Account
```bash
python create_admin.py
```

### Step 3: Verify Database
The file `productivity_planner_multiuser.db` should exist in your project folder.

### Step 4: Don't Delete Database
- The `.gitignore` file prevents `*.db` files from being committed
- **Important**: Don't delete the database file - this is where all your data is stored!
- If you need a fresh start, use `python reset_database.py` instead

### Common Issues:

**Problem**: Tasks disappear after restart
- **Cause**: Database file was deleted or not created
- **Fix**: Run `python init_database.py` again

**Problem**: Can't login
- **Fix**: Run `python create_admin.py` to recreate admin account
- **Login**: username: `thedatadude`, password: `Jacobm1313!`

**Problem**: "Database is locked" error
- **Fix**: Close all other instances of the app
- Or restart your computer

## What You Get (FREE!)

### ✅ Features with Free AI:

1. **Natural Language Task Creation**:
   - "I need to prepare presentation by Monday and call dentist tomorrow"
   - AI creates properly categorized tasks with due dates

2. **Productivity Insights**:
   - Analyzes your completion patterns
   - Suggests improvements
   - Identifies your productive times

3. **Daily Planning**:
   - AI suggests which 5-7 tasks to focus on today
   - Considers priorities and deadlines
   - Balances your workload

4. **Chat Assistant**:
   - Ask productivity questions
   - Get personalized advice
   - Discusses your goals and progress

### 💰 Cost Comparison:

| Provider | Cost | Setup Time | Quality |
|----------|------|------------|---------|
| **Google Gemini** | FREE! | 2 minutes | Excellent |
| **Ollama** | FREE! | 5 minutes | Very Good |
| OpenAI GPT-4 | $5-20/month | 2 minutes | Excellent |

## Example Usage

### Creating Tasks:
```
Input: "This week I need to finish the project report, schedule dentist
appointment, and go to gym 3 times"

AI Creates:
✅ Finish project report (Work, High priority, due Friday)
✅ Schedule dentist appointment (Health, Medium, due tomorrow)
✅ Gym session 1 (Health, Medium, due Monday)
✅ Gym session 2 (Health, Medium, due Wednesday)
✅ Gym session 3 (Health, Medium, due Friday)
```

### Getting Insights:
```
Click "Get Insights" →

AI Analysis:
"Great job completing 85% of your high-priority tasks! I notice you're
strongest on Tuesday and Wednesday. Consider scheduling important tasks
on these days. You have a good balance between work and health activities.
To maintain your streak, try setting up a consistent morning routine."
```

## Troubleshooting

### "AI not configured" message:
1. Make sure `.streamlit/secrets.toml` exists
2. Check the API key has no extra spaces
3. Restart the Streamlit app

### "Rate limit exceeded":
- Google Gemini free tier: 60 requests/minute
- Just wait 1 minute and try again
- Or install Ollama for unlimited local use

### Ollama not working:
1. Make sure Ollama is installed: `ollama --version`
2. Download model: `ollama pull llama2`
3. Check it's running: `ollama list`

## Database Best Practices

To prevent data loss:

1. **Backup your database** periodically:
   ```bash
   copy productivity_planner_multiuser.db productivity_planner_backup.db
   ```

2. **Don't commit to Git** (already in .gitignore)

3. **For cloud deployment**: Use environment variables and a persistent database service

## Support

- Check [AI_SETUP_INSTRUCTIONS.md](./AI_SETUP_INSTRUCTIONS.md) for detailed info
- Review [AI_INTEGRATION_GUIDE.md](./AI_INTEGRATION_GUIDE.md) for technical details

**Start with Google Gemini - it's the easiest and completely FREE!** 🎉
