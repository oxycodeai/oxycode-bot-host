# OXYCODE BOT HOST 👾 - Product Requirements Document

**Version:** 1.0.0
**Date:** August 30, 2026
**Status:** Planning Phase

---

## 1. Product Overview

**OXYCODE BOT HOST** is a mobile-first bot hosting platform designed to run on Android phones via Termux. Users can host, manage, and monitor Telegram and Discord bots directly from their phone's localhost browser — no login required, no cloud servers needed.

### 1.1 Vision
> "Your phone is your server. Your bots run in your pocket."

### 1.2 Target Users
- Telegram bot developers (python-telegram-bot, pyrogram, telethon, aiogram)
- Discord bot developers (discord.py, discord.js)
- Beginners who want to host bots without VPS/cloud costs
- Indian developers using affordable Android phones

### 1.3 Platform
- **Runtime:** Termux (Android)
- **Access:** localhost via phone browser
- **Database:** SQLite (zero config)
- **Backend:** Python Flask

---

## 2. Core Features

### 2.1 Telegram Join Popup (First Launch)

**Description:** On first visit, a modal popup appears asking user to join the OXYCODE AI Telegram channel.

| Element | Details |
|---------|---------|
| Title | "Welcome to OXYCODE BOT HOST 👾" |
| Subtitle | "Must Join Our Telegram Channel" |
| Button | Blue Telegram logo + "JOIN CHANNEL" |
| Button Link | https://t.me/OXYCODEAI |
| Checkbox | "Do not show again" |
| Storage | localStorage flag `oxycode_popup_seen` |
| Trigger | First visit only (unless checkbox unchecked) |

**UI Mockup:**
```
┌─────────────────────────────────┐
│                                 │
│         👾 OXYCODE AI           │
│         BOT HOST                │
│                                 │
│    Must Join Our Telegram       │
│    Channel for Updates          │
│                                 │
│    ┌─────────────────────┐      │
│    │ ✈️ JOIN CHANNEL      │      │
│    └─────────────────────┘      │
│                                 │
│    ☐ Do not show again          │
│                                 │
└─────────────────────────────────┘
```

### 2.2 Main Dashboard

**Description:** The main screen showing all projects and system status.

| Element | Details |
|---------|---------|
| Header | "OXYCODE BOT HOST 👾" + server status indicator |
| Stats Bar | CPU Usage, RAM Usage, Active Bots count |
| Create Button | "+ Create Project" (prominent, top of list) |
| Project List | Cards showing each bot with status, controls |
| Empty State | "No projects yet. Create your first bot!" |

**Project Card:**
```
┌─────────────────────────────────┐
│ 📦 My Telegram Bot              │
│ Status: ● Running | Uptime: 2h  │
│ GitHub: github.com/user/repo    │
│                                 │
│ [▶ Start] [⏹ Stop] [🔄 Restart]│
│ [📝 Editor] [📋 Logs] [🗑 Delete]│
└─────────────────────────────────┘
```

**Status Indicators:**
- 🟢 Green dot = Running
- 🔴 Red dot = Stopped
- 🟡 Yellow dot = Installing dependencies
- 🔵 Blue dot = Starting up
- ⚫ Gray dot = Error

### 2.3 Create Project Flow

**Step 1: Choose Source**
```
┌─────────────────────────────────┐
│  Create New Project             │
├─────────────────────────────────┤
│                                 │
│  Option A: GitHub Repository    │
│  ┌─────────────────────────┐    │
│  │ GitHub URL              │    │
│  │ [___________________]   │    │
│  └─────────────────────────┘    │
│                                 │
│  Option B: Upload Files         │
│  ┌─────────────────────────┐    │
│  │ 📁 Choose Files          │    │
│  └─────────────────────────┘    │
│                                 │
│  Option C: Blank Project        │
│  ┌─────────────────────────┐    │
│  │ Create Empty main.py    │    │
│  └─────────────────────────┘    │
│                                 │
│  [CREATE PROJECT]               │
└─────────────────────────────────┘
```

**Step 2: Auto-Detection (after source selected)**
1. Clone/copy files to `projects/{name}/`
2. Scan for `requirements.txt` (Python) or `package.json` (Node.js)
3. Display detected dependencies to user
4. Auto-install dependencies in background
5. Detect main file (`main.py`, `bot.py`, `app.py`, `index.js`, `bot.js`)
6. Project ready for start

**Step 3: Installation Progress**
```
┌─────────────────────────────────┐
│  Setting up: My Telegram Bot    │
├─────────────────────────────────┤
│  ✅ Files cloned successfully   │
│  ✅ requirements.txt detected   │
│  🔄 Installing dependencies...  │
│     pip install pyTelegramBotAPI│
│     pip install requests        │
│  ⏳ Detecting main file...      │
│                                 │
│  [Cancel]                       │
└─────────────────────────────────┘
```

### 2.4 Bot Process Management

| Action | Behavior |
|--------|----------|
| **Start** | Run `python3 -u main.py` or `node index.js` in subprocess |
| **Stop** | Kill process group (SIGKILL) |
| **Restart** | Stop → Wait 1.5s → Start |
| **Auto-restart** | Optional: restart if process crashes (configurable) |

**Start Flow:**
1. Check if already running → kill existing process
2. Set environment variables (from .env file if exists)
3. Launch subprocess with stdout/stderr capture
4. Track PID in database
5. Start log capture thread
6. Update status to "running"

**Stop Flow:**
1. Kill process group (try `os.killpg` first, fallback to `os.kill`)
2. Remove PID from tracking
3. Update status to "stopped"

### 2.5 File Editor

**Description:** Built-in code editor with syntax highlighting for editing bot source files.

| Feature | Details |
|---------|---------|
| Syntax Highlighting | Python, JavaScript, JSON, HTML, CSS, YAML, .env |
| Line Numbers | Yes |
| Tab Support | Tab key inserts 4 spaces |
| Auto-save | Every 30 seconds (optional) |
| Manual Save | Ctrl+S or Save button |
| Download | Export file to phone storage |
| Theme | Dark theme (default), Light theme (toggle) |
| Font | Monospace (Fira Code / JetBrains Mono) |
| Word Count | Live word/character count |
| Search & Replace | Ctrl+F to find, Ctrl+H to replace |

**Supported Languages:**
- Python (`.py`)
- JavaScript (`.js`)
- JSON (`.json`)
- HTML (`.html`)
- CSS (`.css`)
- YAML (`.yml`, `.yaml`)
- Environment (`.env`)
- Markdown (`.md`)
- Text (`.txt`)

**UI Layout:**
```
┌─────────────────────────────────┐
│ ← Back  |  main.py  |  Save    │
├─────────────────────────────────┤
│  1 │ import telebot              │
│  2 │ bot = telebot.TeleBot(...)  │
│  3 │                             │
│  4 │ @bot.message_handler(...)   │
│  5 │ def handle(msg):            │
│  6 │     bot.reply_to(msg, "Hi") │
│  7 │                             │
│  8 │ bot.polling()               │
├─────────────────────────────────┤
│  Ln 8, Col 1  |  45 words  | UTF-8 │
└─────────────────────────────────┘
```

### 2.6 Live Logs Viewer

**Description:** Real-time log viewer showing bot output.

| Feature | Details |
|---------|---------|
| Auto-scroll | Follows latest output |
| Pause scroll | Tap to pause, tap again to resume |
| Clear logs | Button to clear log history |
| Download logs | Export as .log file |
| Timestamp | Each line prefixed with time |
| Color coding | stdout=green, stderr=red, info=cyan |
| Max size | Last 50KB displayed (older truncated) |

**Log Display:**
```
┌─────────────────────────────────┐
│ ← Back  |  Bot Logs  |  Clear  │
├─────────────────────────────────┤
│ [12:00:01] 🟢 Bot starting...   │
│ [12:00:02] ✅ Connected to API  │
│ [12:00:05] 📨 Message received  │
│ [12:00:05] 📤 Reply sent        │
│ [12:01:30] ⚠️ Rate limit: 2s    │
│ [12:02:00] 📨 Message received  │
└─────────────────────────────────┘
```

### 2.7 GitHub Integration

| Action | Behavior |
|--------|----------|
| **Clone by URL** | `git clone {url}` into project folder |
| **Auto-detect** | Scan for requirements.txt / package.json |
| **Re-sync** | Pull latest changes from GitHub |
| **Backup** | Push local changes back to GitHub |

**Supported URL Formats:**
- `https://github.com/user/repo`
- `https://github.com/user/repo.git`
- `git@github.com:user/repo.git`

### 2.8 Environment Variable Manager

**Description:** Edit .env files for bot tokens and config.

```
┌─────────────────────────────────┐
│ ← Back  |  .env Editor  | Save │
├─────────────────────────────────┤
│ BOT_TOKEN=123456:ABC-DEF...    │
│ API_KEY=your_api_key_here       │
│ DATABASE_URL=mongodb://...      │
│ OWNER_ID=123456789              │
│                                 │
│ [+ Add Variable]                │
└─────────────────────────────────┘
```

### 2.9 System Stats

**Real-time monitoring displayed on dashboard:**

| Metric | Source |
|--------|--------|
| CPU Usage | `/proc/loadavg` |
| RAM Usage | `/proc/meminfo` |
| Storage Used | `os.walk()` on projects folder |
| Active Bots | Count from database |
| Uptime | Time since Flask server started |
| Network | `/proc/net/dev` |

### 2.10 Additional Features

| Feature | Description |
|---------|-------------|
| **Download as ZIP** | Download entire project as .zip file |
| **Delete Project** | Remove project files and database entry |
| **Rename Project** | Change project name |
| **Duplicate Project** | Clone project with new name |
| **Dark/Light Theme** | Toggle between themes |
| **Search Projects** | Filter by name or status |
| **Bot Auto-Restart** | Restart crashed bots automatically |
| **Multi-language** | Python + Node.js bot support |
| **File Upload** | Upload files directly from phone |
| **File Download** | Download individual files |

---

## 3. User Flow Diagrams

### 3.1 First Time User
```
Open localhost:5000
    ↓
Telegram Join Popup appears
    ↓
Click "Join Channel" → Opens Telegram
    ↓
Check "Do not show again" → Close popup
    ↓
Empty Dashboard shown
    ↓
Click "+ Create Project"
    ↓
Choose: GitHub URL / Upload / Blank
    ↓
Project created + dependencies installed
    ↓
Click "Start" → Bot runs!
```

### 3.2 Returning User
```
Open localhost:5000
    ↓
Dashboard with all projects
    ↓
See status: Running / Stopped / Error
    ↓
Start/Stop/Restart as needed
    ↓
Edit files / View logs
```

---

## 4. Non-Functional Requirements

### 4.1 Performance
- Dashboard loads in < 2 seconds
- Log refresh every 2 seconds
- Stats refresh every 5 seconds
- Max 10 concurrent bot processes

### 4.2 Security
- No login required (local access only)
- No remote access by default
- GitHub tokens stored in .env (never in code)
- Bot processes run in isolated folders

### 4.3 Compatibility
- Android 8.0+ (Termux)
- Python 3.8+
- Node.js 16+ (optional)
- Modern browsers (Chrome, Firefox, Edge)

### 4.4 Resource Limits
- Max project size: 100MB per project
- Max total storage: 500MB (configurable)
- Max log size: 50KB per bot
- Max concurrent processes: 10

---

## 5. Success Metrics

| Metric | Target |
|--------|--------|
| Time to first bot running | < 2 minutes |
| Dashboard load time | < 2 seconds |
| Bot crash recovery | < 5 seconds |
| User can host 5 bots simultaneously | Yes |
| Works on budget phone (2GB RAM) | Yes |

---

## 6. Out of Scope (v1.0)

- User authentication / login system
- Multi-user support
- Cloud hosting / VPS deployment
- Webhook support
- Database hosting (MongoDB, PostgreSQL)
- Docker containerization
- Web-based SSH terminal
- Mobile app (native)
- Payment / subscription system

---

## 7. Future Features (v2.0)

- User login with GitHub OAuth
- Multi-user support
- Cloud deployment option
- Bot templates (starter bots)
- Webhook support
- Bot analytics (message count, uptime)
- Auto-deploy from GitHub push
- Bot marketplace
- Docker support
- Custom domain mapping

---

*Document prepared for OXYCODE BOT HOST v1.0*
*Last updated: August 30, 2026*
