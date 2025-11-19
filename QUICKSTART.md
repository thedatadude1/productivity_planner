# 🚀 Quick Start - Productivity Planner with FREE AI

## 1. Install Dependencies (1 minute)

```bash
pip install -r requirements.txt
```

## 2. Initialize Database (30 seconds)

```bash
python init_database.py
python create_admin.py
```

## 3. Setup FREE AI (2 minutes)

### Option A: Google Gemini (Recommended)

1. Get FREE key: https://makersuite.google.com/app/apikey
2. Create `.streamlit/secrets.toml`:
   ```toml
   GOOGLE_API_KEY = "your-key-here"
   ```

### Option B: Ollama (Local, No API Key)

1. Install from https://ollama.ai
2. Run: `ollama pull llama2`
3. Done! (No secrets needed)

## 4. Run the App

```bash
streamlit run app_multiuser.py
```

## 5. Login

- **Username**: `thedatadude`
- **Password**: `Jacobm1313!`

## 6. Try AI Features

Go to "🤖 AI Assistant" tab and type:
```
I need to finish project report by Friday, schedule dentist appointment,
and go to the gym 3 times this week
```

Watch AI create all your tasks automatically! 🎉

---

## Troubleshooting

**Data keeps deleting?**
- Run: `python init_database.py`
- Check file `productivity_planner_multiuser.db` exists

**Can't login?**
- Run: `python create_admin.py`
- Use credentials above

**AI not working?**
- Check `.streamlit/secrets.toml` exists
- See [FREE_AI_SETUP.md](FREE_AI_SETUP.md) for detailed help

---

**That's it! You're ready to be productive with FREE AI! 🚀**
