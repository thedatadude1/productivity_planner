# 📊 Data Persistence Information

## Current Setup

Your productivity planner uses **SQLite** database stored in:
- **File**: `productivity_planner_multiuser.db`
- **Location**: App root directory (absolute path)
- **Connection**: 30-second timeout for reliability

## ⚠️ Important: Streamlit Cloud Limitations

### SQLite on Streamlit Cloud:
- **Temporary Storage**: Data persists for ~5-7 days
- **Reset on Redeploy**: App updates may reset data
- **Not Recommended**: For long-term production use

### Your Data Safety Options:

#### Option 1: Download Backups (Manual)
1. Not easily accessible on Streamlit Cloud
2. Would require adding export functionality

#### Option 2: PostgreSQL (Recommended) ✅
**Neon PostgreSQL** - FREE tier includes:
- ✅ 3GB storage
- ✅ Permanent data persistence
- ✅ Automatic backups
- ✅ No credit card required

**Setup (5 minutes):**
1. Sign up: https://neon.tech
2. Create new project
3. Copy connection string
4. Add to Streamlit Secrets:
   ```toml
   DATABASE_URL = "postgresql://username:password@host/database"
   ```
5. Reply "migrate to PostgreSQL" and I'll update the code

## Current Status

✅ **Database Features Working:**
- Multi-user support
- Task management
- Goals tracking
- Daily journal entries
- Achievements system
- Analytics & insights

✅ **Recent Fixes:**
- Absolute path for database file
- 30-second connection timeout
- Proper achievement updates on task completion
- Fireworks celebration effect

## What Happens to Your Data

### On Streamlit Cloud (Current):
- Data stored in ephemeral container
- Survives app refreshes
- **May be lost on**:
  - App redeployment
  - Streamlit Cloud maintenance
  - After ~5-7 days of inactivity

### With PostgreSQL (Recommended):
- Data stored permanently in cloud database
- Survives all app updates
- Professional-grade persistence
- Never lost unless you delete it

## Recommendation

For your use case with completed tasks and ongoing productivity tracking, I **strongly recommend** migrating to PostgreSQL to ensure you never lose your data.

Let me know if you'd like me to set this up!
