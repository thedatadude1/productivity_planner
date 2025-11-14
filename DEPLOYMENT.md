# Deployment Guide for Ultimate Productivity Planner

This guide covers multiple deployment options for hosting your productivity planner online.

---

## Option 1: Streamlit Community Cloud (Recommended - FREE)

**Best for**: Free hosting with minimal setup

### Prerequisites
- GitHub account
- Git installed on your computer

### Steps:

1. **Initialize Git Repository** (if not already done)
   ```bash
   cd productivity_planner
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Create GitHub Repository**
   - Go to [github.com](https://github.com) and create a new repository
   - Name it something like `productivity-planner`
   - Don't initialize with README (we already have files)

3. **Push to GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/productivity-planner.git
   git branch -M main
   git push -u origin main
   ```

4. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your repository, branch (main), and main file (`app_multiuser.py`)
   - Click "Deploy"

5. **Your app will be live at**: `https://YOUR-USERNAME-productivity-planner.streamlit.app`

### Important Notes:
- Use `app_multiuser.py` for multi-user support with authentication
- The free tier has some limitations (resources, concurrent users)
- Database is SQLite (stored in container, may reset on redeploy)

---

## Option 2: Heroku (Good for Production)

**Best for**: More control, custom domains, better performance

### Prerequisites
- Heroku account (free tier available)
- Heroku CLI installed

### Steps:

1. **Create Procfile**
   ```bash
   echo "web: streamlit run app_multiuser.py --server.port=$PORT --server.address=0.0.0.0" > Procfile
   ```

2. **Create setup.sh**
   ```bash
   cat > setup.sh << EOF
   mkdir -p ~/.streamlit/
   echo "[server]
   headless = true
   port = \$PORT
   enableCORS = false
   " > ~/.streamlit/config.toml
   EOF
   ```

3. **Update Procfile**
   ```
   web: sh setup.sh && streamlit run app_multiuser.py
   ```

4. **Deploy to Heroku**
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   heroku open
   ```

5. **For persistent database**, upgrade to PostgreSQL:
   - Install `psycopg2` and modify database code
   - Add PostgreSQL addon in Heroku

---

## Option 3: Railway (Easy & Modern)

**Best for**: Quick deployment with modern UI

### Steps:

1. **Go to** [railway.app](https://railway.app)
2. **Sign in with GitHub**
3. **Click "New Project" → "Deploy from GitHub repo"**
4. **Select your repository**
5. **Add environment variables if needed**
6. **Railway auto-detects Streamlit and deploys**

**Your app will be live at**: `https://your-app-name.railway.app`

---

## Option 4: Google Cloud Run (Scalable)

**Best for**: High traffic, enterprise use

### Steps:

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install -r requirements.txt

   COPY . .

   EXPOSE 8080

   CMD ["streamlit", "run", "app_multiuser.py", "--server.port=8080", "--server.address=0.0.0.0"]
   ```

2. **Build and Deploy**
   ```bash
   gcloud run deploy productivity-planner \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

---

## Option 5: DigitalOcean App Platform

**Best for**: Balance of simplicity and control

### Steps:

1. **Connect GitHub** to DigitalOcean
2. **Create new App**
3. **Select your repository**
4. **Configure**:
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `streamlit run app_multiuser.py --server.port=8080 --server.address=0.0.0.0`
5. **Deploy**

---

## Database Considerations for Production

### SQLite Limitations:
- File-based database
- May reset on container restarts
- Not ideal for high concurrency

### Upgrade to PostgreSQL (Recommended for production):

1. **Update requirements.txt**
   ```
   streamlit>=1.31.0
   pandas>=2.0.0
   plotly>=5.18.0
   psycopg2-binary>=2.9.0
   sqlalchemy>=2.0.0
   ```

2. **Modify database connection** (example):
   ```python
   import os
   from sqlalchemy import create_engine

   # Use PostgreSQL if DATABASE_URL is set, otherwise SQLite
   DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///productivity_planner.db')

   # PostgreSQL connection
   engine = create_engine(DATABASE_URL)
   ```

3. **Add DATABASE_URL** environment variable in your hosting platform

---

## Security Best Practices

1. **Use Environment Variables** for sensitive data:
   ```python
   import os
   SECRET_KEY = os.getenv('SECRET_KEY', 'default-key-for-dev')
   ```

2. **Enable HTTPS** (most platforms do this automatically)

3. **Use stronger password hashing**:
   - Install `bcrypt`: `pip install bcrypt`
   - Replace `hashlib.sha256` with `bcrypt.hashpw()`

4. **Add rate limiting** to prevent abuse

5. **Regular backups** of your database

---

## Custom Domain Setup

Most platforms allow custom domains:

1. **Purchase domain** (Namecheap, Google Domains, etc.)
2. **Add domain** in your hosting platform settings
3. **Update DNS records** as instructed
4. **Enable SSL/HTTPS** (usually automatic)

---

## Cost Comparison

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| Streamlit Cloud | 1 private app | $20/month | Quick demos |
| Heroku | Limited hours | $7/month | Small apps |
| Railway | $5 credit | Pay-as-you-go | Modern stack |
| Google Cloud Run | 2M requests/mo | Pay-as-you-go | High scale |
| DigitalOcean | $0 | $5/month | Predictable cost |

---

## Monitoring & Analytics

1. **Streamlit built-in**: View usage in Streamlit Cloud dashboard
2. **Google Analytics**: Add tracking code to custom HTML
3. **Sentry**: Error tracking for production apps
4. **Uptime monitoring**: UptimeRobot, Pingdom

---

## Quick Start: Deploy to Streamlit Cloud NOW

```bash
# 1. Navigate to your project
cd productivity_planner

# 2. Initialize git (if needed)
git init

# 3. Create .gitignore to exclude database
echo "*.db" > .gitignore

# 4. Commit files
git add .
git commit -m "Initial commit for deployment"

# 5. Create GitHub repo and push
# (Use GitHub web interface or GitHub CLI)

# 6. Go to share.streamlit.io and deploy!
```

---

## Troubleshooting

**App won't start:**
- Check requirements.txt has all dependencies
- Verify Python version compatibility
- Check logs in hosting platform

**Database resets:**
- Upgrade to PostgreSQL
- Use persistent volume (if available)

**Slow performance:**
- Optimize database queries
- Add caching with `@st.cache_data`
- Upgrade hosting tier

**Users can't login:**
- Check database is persisting
- Verify password hashing is consistent
- Check for typos in username/password

---

## Next Steps

1. ✅ Choose a deployment platform
2. ✅ Push code to GitHub
3. ✅ Deploy your app
4. ✅ Share the URL with users
5. ✅ Monitor usage and performance
6. ✅ Collect feedback and iterate

**Need help?** Check platform-specific documentation or community forums!
