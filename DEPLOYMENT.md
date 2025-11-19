# 🚀 Deployment Guide - Streamlit Cloud

## Quick Deploy (5 Minutes)

### Step 1: Deploy to Streamlit Cloud

1. Go to: https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select:
   - Repository: `thedatadude1/productivity_planner`
   - Branch: `main`
   - Main file: `app_multiuser.py`
5. Click "Deploy"

### Step 2: Add FREE AI (Optional)

1. Get FREE Google Gemini key: https://makersuite.google.com/app/apikey
2. In your app settings → "Secrets"
3. Add:
```toml
GOOGLE_API_KEY = "your-free-key-here"
```
4. Save and app will restart

### Step 3: Login

- Username: `thedatadude`
- Password: `Jacobm1313!`

**That's it! Your app is live!** 🎉

---

## Important: Data Persistence

⚠️ **Current Setup**: Using SQLite (data resets when app restarts ~every 5-7 days)

### For Persistent Data (Recommended):

Use **Neon PostgreSQL** (FREE):
1. Sign up: https://neon.tech
2. Create project
3. Copy connection string
4. Add to Streamlit Secrets:
```toml
DATABASE_URL = "postgresql://user:pass@host/db"
```
5. Let me know and I'll update the code to use PostgreSQL

---

## After Deployment

Your app URL: `https://[app-name].streamlit.app`

### Features Working:
- ✅ Task management
- ✅ Goals tracking
- ✅ Daily journal
- ✅ Analytics & charts
- ✅ Achievements
- ✅ AI Assistant (if you add API key)

### To Update:
```bash
git add -A
git commit -m "your message"
git push origin main
```
Streamlit auto-deploys in ~2 minutes!

---

## Troubleshooting

**"Module not found"**: Check requirements.txt is in repo root

**Database issues**: Normal with SQLite on cloud - consider PostgreSQL

**AI not working**: Add GOOGLE_API_KEY to Streamlit Secrets

---

Need help? Check the logs in your Streamlit Cloud dashboard!
