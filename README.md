# Ultimate Productivity Planner

A comprehensive, beautiful, and feature-rich productivity management system built with Streamlit. This app combines task management, goal tracking, daily journaling, achievement systems, and analytics to help you stay organized, motivated, and productive.

## Features

### Dashboard
- **Real-time statistics** showing your productivity metrics
- **Current streak tracking** to maintain momentum
- **Quick view** of today's urgent tasks and active goals
- **Daily motivational quotes** to keep you inspired

### Task Management
- Create, update, and delete tasks with ease
- Categorize tasks (Work, Personal, Health, Learning, Finance, Other)
- Set priorities (High, Medium, Low) with visual indicators
- Track estimated hours and actual progress
- Add custom tags for better organization
- Filter and sort tasks by status, category, and date
- Visual status tracking (Pending, In Progress, Completed)

### Goal Tracking
- Set long-term goals with target dates
- Track progress with visual progress bars (0-100%)
- Monitor multiple active goals simultaneously
- Celebrate milestone achievements when goals are completed

### Calendar View
- **Timeline visualization** of all your tasks
- **Week view** showing daily task breakdown
- Color-coded by priority for quick identification
- Plan ahead and avoid deadline conflicts

### Daily Journal
- **Mood tracking** with historical trends (1-10 scale)
- **Gratitude practice** to maintain positive mindset
- Document daily highlights and wins
- Record challenges and learnings for growth
- Plan tomorrow's top 3 priorities
- Visual mood trend chart to track emotional patterns

### Achievement System
- Earn badges for completing milestones:
  - First Steps (5 tasks)
  - Getting Started (25 tasks)
  - Halfway Hero (50 tasks)
  - Century Club (100 tasks)
  - Week Warrior (7-day streak)
  - Monthly Master (30-day streak)
- Track progress toward next achievement
- Celebrate your wins with visual feedback

### Analytics Dashboard
- **Task completion trends** over the last 30 days
- **Category breakdown** showing where you spend your time
- **Priority distribution** to balance workload
- **Productivity metrics** including:
  - Average daily completion rate
  - Overall completion percentage
  - Total hours invested
- **Personalized motivational feedback** based on performance

## Installation

1. **Clone or download this repository**

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser** and navigate to the URL shown in the terminal (typically `http://localhost:8501`)

## How to Use

### Getting Started

1. **Dashboard**: Start here to get an overview of your productivity
2. **Add Tasks**: Navigate to "Tasks" and create your first task with all relevant details
3. **Set Goals**: Go to "Goals" and define what you want to achieve
4. **Daily Journal**: Reflect on your day and track your mood
5. **Monitor Progress**: Check "Analytics" to see your productivity trends

### Best Practices

- **Start each day** by reviewing your dashboard and checking today's tasks
- **Set realistic priorities** - not everything can be high priority
- **Use categories** to separate different areas of your life
- **Journal daily** to maintain self-awareness and track emotional patterns
- **Review analytics weekly** to identify patterns and optimize productivity
- **Celebrate achievements** - acknowledge your progress!

### Tips for Maximum Productivity

1. **Break large tasks** into smaller, actionable items
2. **Use estimated hours** to avoid overcommitting
3. **Maintain your streak** for consistent progress
4. **Review and update goals** regularly
5. **Use tags** for quick filtering (e.g., "urgent", "meeting", "review")
6. **Reflect in your journal** - it helps identify what's working and what's not

## Data Storage

All your data is stored locally in an SQLite database (`productivity_planner.db`) in the same directory as the app. Your data is:
- **Private** - never sent to external servers
- **Persistent** - survives app restarts
- **Portable** - can be backed up by copying the database file

## Customization

You can customize the app by modifying:
- **Categories**: Edit the category list in the `show_tasks()` function
- **Motivational quotes**: Add your own quotes to the `MOTIVATIONAL_QUOTES` list
- **Achievements**: Modify thresholds and create new achievements in `check_achievements()`
- **Styling**: Adjust the CSS in the custom styles section at the top of the file

## Technical Details

- **Framework**: Streamlit (Python web framework)
- **Database**: SQLite (local, file-based)
- **Visualization**: Plotly for interactive charts
- **Data Processing**: Pandas for data manipulation

## Troubleshooting

**App won't start:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that you're using Python 3.8 or higher

**Data not saving:**
- Ensure you have write permissions in the app directory
- Check that the database file isn't locked by another process

**Charts not displaying:**
- Ensure Plotly is installed correctly
- Try refreshing the browser

## Future Enhancements

Potential features to add:
- Task dependencies and subtasks
- Pomodoro timer integration
- Export data to CSV/PDF
- Recurring tasks and reminders
- Team collaboration features
- Mobile-responsive design improvements
- Integration with calendar APIs (Google Calendar, Outlook)
- AI-powered task prioritization
- Habit tracking module

## License

This project is open source and available for personal and educational use.

## Support

If you encounter any issues or have suggestions for improvements, feel free to modify the code to suit your needs!

---

**Made with love to help you achieve your goals and stay motivated!**

Remember: *"The secret of getting ahead is getting started."* - Mark Twain
