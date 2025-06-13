# Gmail Follow-up Manager - Step-by-Step Installation Guide

This guide will walk you through the complete installation process for the Gmail Follow-up Manager application.

## 📋 Prerequisites Checklist

Before starting, ensure you have:
- [ ] Python 3.12 or higher installed
- [ ] `uv` package manager installed (or pip as fallback)
- [ ] A Google account with Gmail access
- [ ] Administrative access to create a Google Cloud Project

## 🚀 Step-by-Step Installation

### Step 1: Install Python and uv

#### Install Python 3.12+
1. **Windows**: Download from [python.org](https://www.python.org/downloads/)
2. **macOS**: Use Homebrew: `brew install python@3.12`
3. **Linux**: Use your package manager: `sudo apt install python3.12`

#### Install uv (Recommended)
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2: Download and Setup Project

1. **Download the project** (extract the ZIP file you received)
2. **Open terminal/command prompt** in the project directory
3. **Verify the structure**:
   ```
   gmail-followup-manager/
   ├── app.py
   ├── pyproject.toml
   ├── src/
   └── ... (other files)
   ```

### Step 3: Install Dependencies

In the project directory, run:
```bash
uv sync
```

If you don't have `uv`, create a virtual environment and use pip:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Step 4: Google Cloud Setup (CRITICAL)

#### 4.1 Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: "Gmail Follow-up Manager"
4. Click "Create"

#### 4.2 Enable Required APIs
1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for and enable:
   - **Gmail API** (click "Enable")
   - **Google Calendar API** (click "Enable")

#### 4.3 Create OAuth 2.0 Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. If prompted, configure OAuth consent screen:
   - Choose "External" user type
   - Fill in app name: "Gmail Follow-up Manager"
   - Add your email as developer contact
   - Save and continue through all steps
4. Back to "Create OAuth 2.0 Client ID":
   - Application type: "Desktop application"
   - Name: "Gmail Follow-up Manager"
   - Click "Create"
5. **Download the JSON file**
6. **Rename it to `credentials.json`**
7. **Place it in your project root directory**

### Step 5: Environment Configuration

Create a `.env` file in the project root:

```env
# Copy this content exactly
DATA_DIR=data
EXPORTS_DIR=data/exports
GOOGLE_CREDENTIALS_FILE=credentials.json
APP_NAME=Gmail Follow-up Manager
DEFAULT_LOOKBACK_DAYS=30
MAX_RESULTS=200
PAGE_TITLE=Gmail Follow-up Manager
PAGE_ICON=📧
LAYOUT=wide
MAX_BACKUPS=10
AUTO_BACKUP=true
OAUTH_PORT_GMAIL=8080
OAUTH_PORT_CALENDAR=8081
```

### Step 6: First Run

1. **Start the application**:
   ```bash
   uv run streamlit run app.py
   ```

2. **Browser will open** automatically at `http://localhost:8501`

3. **First-time authentication**:
   - Click "Re-authenticate" if prompted
   - Browser will open Google OAuth page
   - Sign in with your Google account
   - Grant permissions for Gmail (read-only)
   - Grant permissions for Calendar (create events)
   - You'll see "Authentication successful" message

4. **Verify setup**:
   - You should see the Gmail Follow-up Manager interface
   - Check that Gmail connection shows ✅
   - Calendar connection should also show ✅

## 🔧 Configuration and Usage

### Initial Configuration

1. **Sidebar Settings**:
   - Set your preferred keywords (e.g., "interview,follow up,proposal")
   - Adjust lookback days (default: 30)
   - Configure reminder settings

2. **Test the Search**:
   - Go to "Search" tab
   - Select "SENT" label
   - Click "Search Emails"
   - You should see your sent emails

### Daily Usage Workflow

1. **Search for emails** needing follow-up
2. **Review and categorize** by priority and status
3. **Create calendar reminders** for important follow-ups
4. **Track responses** and update status
5. **Export data** for reporting if needed

## 🐛 Troubleshooting

### Common Issues and Solutions

#### "Module not found" errors
```bash
# Reinstall dependencies
uv sync --reinstall
```

#### "Credentials file not found"
- Ensure `credentials.json` is in the project root
- Check the file name is exactly `credentials.json`
- Verify the file is not empty

#### "Authentication failed"
1. Delete token files: `token_gmail.pickle` and `token_calendar.pickle`
2. Restart the app
3. Re-authenticate when prompted

#### "API not enabled" errors
- Go back to Google Cloud Console
- Verify Gmail API and Calendar API are enabled
- Wait a few minutes for changes to propagate

#### Port conflicts
If port 8501 is in use:
```bash
uv run streamlit run app.py --server.port 8502
```

### Getting Help

1. **Check the logs** in the terminal where you ran the app
2. **Verify your setup** against this guide
3. **Test with a simple search** first
4. **Check Google Cloud Console** for API quotas and errors

## 📊 Performance Optimization

### For Better Performance:
- **Limit search scope**: Use specific date ranges
- **Use keywords**: Filter emails with relevant keywords
- **Regular maintenance**: Clean up old data periodically
- **Backup management**: Keep only recent backups

### Recommended Settings:
- **Lookback days**: 30-60 for regular use
- **Max results**: 100-200 for good performance
- **Keywords**: Be specific to your use case

## 🔒 Security Notes

- **Credentials**: Keep `credentials.json` secure and private
- **Local storage**: All data stays on your computer
- **Permissions**: App only reads Gmail, doesn't modify emails
- **Backup**: Regular backups are created automatically

## 📞 Support

If you encounter issues:

1. **Double-check** each step in this guide
2. **Verify** Google Cloud setup is complete
3. **Test** with a simple email search first
4. **Check** that all required files are in place

Remember: The most common issues are related to Google Cloud setup and credentials file placement.

---

**Success Indicators:**
- ✅ App starts without errors
- ✅ Gmail connection established
- ✅ Calendar connection established
- ✅ Can search and display emails
- ✅ Can create calendar reminders

Once you see all these working, you're ready to use the Gmail Follow-up Manager!

