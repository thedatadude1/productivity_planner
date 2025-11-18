# AI Assistant Setup Instructions

The productivity planner now includes an AI Assistant powered by OpenAI GPT-4 for natural language task creation, productivity insights, and daily planning.

## Features

- **Natural Language Task Creation**: Describe your tasks in plain English and let AI create structured tasks
- **Productivity Insights**: Get AI-powered analysis of your productivity patterns
- **Daily Planning**: AI suggests which tasks to focus on today
- **Chat Assistant**: Ask questions and get personalized productivity advice

## Setup Steps

### 1. Get an OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up or log in to your account
3. Navigate to API Keys
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)

### 2. Configure the API Key

#### For Local Development:

1. Navigate to the `.streamlit` directory in the project
2. Copy the example file:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
3. Edit `.streamlit/secrets.toml` and add your API key:
   ```toml
   OPENAI_API_KEY = "sk-your-actual-api-key-here"
   ```
4. Save the file (it's already in `.gitignore` so it won't be committed)

#### For Streamlit Cloud Deployment:

1. Go to your app on [Streamlit Cloud](https://share.streamlit.io/)
2. Click on your app settings (gear icon)
3. Navigate to "Secrets" in the left sidebar
4. Add your secret:
   ```toml
   OPENAI_API_KEY = "sk-your-actual-api-key-here"
   ```
5. Click "Save"

### 3. Install Dependencies

Make sure you have the latest dependencies installed:

```bash
pip install -r requirements.txt
```

The `requirements.txt` now includes:
- `openai>=1.0.0` - OpenAI Python library

### 4. Run the App

```bash
streamlit run app_multiuser.py
```

Navigate to the "🤖 AI Assistant" tab to start using the AI features!

## Cost Information

### OpenAI GPT-4 Pricing (as of 2025):
- Task creation: ~$0.01-0.02 per request
- Insights generation: ~$0.01-0.03 per request
- Chat messages: ~$0.005-0.02 per message
- **Estimated monthly cost**: $5-20 for regular use

### Tips to Minimize Costs:
1. Create multiple tasks in one request instead of separate requests
2. Generate insights weekly instead of daily
3. Ask clear, specific questions to get concise responses
4. Consider using GPT-3.5-turbo for lower costs (change `model="gpt-4"` to `model="gpt-3.5-turbo"` in the code)

## Alternative AI Options

If you prefer not to use OpenAI, see [AI_INTEGRATION_GUIDE.md](./AI_INTEGRATION_GUIDE.md) for alternatives:
- **Google Gemini**: Free tier available, cheaper than OpenAI
- **Ollama**: Completely free, runs locally, no API key needed

## Usage Examples

### Creating Tasks with Natural Language:

**Input:**
```
I need to prepare a presentation for Monday's meeting, call the dentist tomorrow,
and finish the project report by Friday afternoon. Also schedule time to exercise
3 times this week.
```

**AI will create:**
- "Prepare presentation for Monday's meeting" (Work, High priority, due Monday)
- "Call dentist" (Health, Medium priority, due tomorrow)
- "Finish project report" (Work, High priority, due Friday)
- "Exercise session 1" (Health, Medium priority)
- "Exercise session 2" (Health, Medium priority)
- "Exercise session 3" (Health, Medium priority)

### Getting Productivity Insights:

The AI analyzes your:
- Task completion patterns
- Category distribution
- Priority management
- Completion rates

And provides actionable insights like:
- "You're completing 85% of your high-priority tasks - great focus!"
- "Consider balancing work tasks with more health-related activities"
- "Your completion rate is highest on Tuesday and Wednesday"

### Daily Planning:

AI reviews your pending tasks and suggests:
- Which 5-7 tasks to focus on today
- Optimal task order based on priorities and deadlines
- Balanced workload considering estimated hours
- Encouraging tips to stay motivated

## Troubleshooting

### "AI assistant is not configured" Error:
- Make sure `secrets.toml` exists with your API key
- Verify the API key starts with `sk-`
- Restart the Streamlit app after adding secrets

### "Invalid API Key" Error:
- Check if your API key is correct
- Verify your OpenAI account has credits
- Make sure there are no extra spaces in the key

### "Rate Limit Exceeded" Error:
- You've hit OpenAI's rate limits
- Wait a few minutes and try again
- Consider upgrading your OpenAI plan

### High Costs:
- Monitor your usage at [OpenAI Platform](https://platform.openai.com/usage)
- Set up usage limits in your OpenAI account settings
- Consider switching to GPT-3.5-turbo for lower costs

## Security Notes

- Never commit your `secrets.toml` file to version control
- The file is already in `.gitignore` for protection
- Don't share your API key publicly
- Rotate your API key if it's ever exposed
- Monitor your OpenAI usage regularly

## Support

For questions or issues:
- Check [AI_INTEGRATION_GUIDE.md](./AI_INTEGRATION_GUIDE.md) for detailed information
- Visit [OpenAI Documentation](https://platform.openai.com/docs)
- Review [Streamlit Secrets Documentation](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
