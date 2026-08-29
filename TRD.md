# OXYCODE BOT HOST 👾 - Technical Requirements Document

**Version:** 1.0.0
**Date:** August 30, 2026
**Status:** Planning Phase

---

## 1. Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Runtime** | Python | 3.8+ | Backend server |
| **Web Framework** | Flask | 3.x | HTTP server, routes, templates |
| **Database** | SQLite | 3.x | Persistent storage (zero config) |
| **Template Engine** | Jinja2 | 3.x | HTML rendering |
| **Frontend** | HTML5 + Tailwind CSS | CDN | Mobile-first UI |
| **Code Editor** | CodeMirror 6 | CDN | Syntax highlighting |
| **Charts** | Chart.js | CDN | CPU/RAM graphs |
| **Icons** | Font Awesome | 6.x CDN | Icon library |
| **JS Utils** | Vanilla JS | ES6 | Frontend logic |
| **Process Mgmt** | subprocess | stdlib | Bot process control |
| **Threading** | threading | stdlib | Background tasks |
| **Git** | gitpython / subprocess | - | GitHub clone/pull |

---

## 2. Project Structure

```
oxycode-bot-host/
├── app.py                      # Main Flask application (all routes)
├── database.py                 # SQLite database operations
├── process_manager.py          # Bot start/stop/restart logic
├── github_handler.py           # GitHub clone/pull/backup
├── auto_installer.py           # requirements.txt / package.json parser + installer
├── config.py                   # App configuration constants
├── requirements.txt            # Python dependencies (flask, requests)
├── start.sh                    # Termux startup script
│
├── static/
│   ├── css/
│   │   └── style.css           # Global dark theme styles
│   ├── js/
│   │   ├── app.js              # Dashboard logic (fetch, stats, project list)
│   │   ├── editor.js           # CodeMirror editor initialization
│   │   ├── popup.js            # Telegram join popup logic
│   │   └── logs.js             # Live log viewer logic
│   └── img/
│       └── logo.png            # OXYCODE BOT HOST logo
│
├── templates/
│   ├── base.html               # Base template (header, nav, scripts)
│   ├── dashboard.html          # Main dashboard (project list + stats)
│   ├── editor.html             # File editor page
│   ├── logs.html               # Live logs viewer page
│   ├── create.html             # Create project page
│   ├── env_editor.html         # .env file editor page
│   └── components/
│       ├── popup.html          # Telegram join popup component
│       ├── project_card.html   # Project card component
│       └── stats_bar.html      # System stats bar component
│
├── projects/                   # User bot projects (auto-created)
│   └── {project_name}/
│       ├── main.py             # Bot entry point
│       ├── requirements.txt    # Python dependencies
│       ├── package.json        # Node.js dependencies (if applicable)
│       ├── .env                # Environment variables
│       └── .logs/
│           └── output.log      # Bot stdout/stderr log
│
├── bot_host.db                 # SQLite database file (auto-created)
└── uploads/                    # Temporary file upload area
```

---

## 3. Database Schema (SQLite)

### 3.1 Projects Table

```sql
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    source_type TEXT DEFAULT 'blank',        -- 'github', 'upload', 'blank'
    github_url TEXT DEFAULT '',               -- GitHub repo URL (if source_type='github')
    main_file TEXT DEFAULT 'main.py',        -- Entry point filename
    runtime TEXT DEFAULT 'python',           -- 'python' or 'node'
    status TEXT DEFAULT 'stopped',           -- 'stopped','running','installing','starting','error'
    pid INTEGER DEFAULT 0,                   -- Process ID (0 if not running)
    port INTEGER DEFAULT 0,                  -- Port number (if web server)
    auto_restart INTEGER DEFAULT 0,          -- 0=off, 1=on
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_started TIMESTAMP,
    last_stopped TIMESTAMP,
    error_message TEXT DEFAULT ''            -- Last error message
);
```

### 3.2 Settings Table

```sql
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Default settings
INSERT OR IGNORE INTO settings (key, value) VALUES
    ('popup_seen', 'false'),
    ('theme', 'dark'),
    ('max_projects', '10'),
    ('auto_restart_default', 'false'),
    ('log_max_size_kb', '50');
```

### 3.3 Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
```

---

## 4. API Routes

### 4.1 Page Routes

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Dashboard (project list + stats) |
| GET | `/create` | Create project page |
| GET | `/editor/<project>/<filepath>` | File editor page |
| GET | `/logs/<project>` | Live logs viewer |
| GET | `/env/<project>` | .env editor page |

### 4.2 API Routes (JSON)

| Method | Route | Body/Params | Description |
|--------|-------|-------------|-------------|
| GET | `/api/stats` | - | System stats (CPU, RAM, disk) |
| GET | `/api/projects` | - | List all projects |
| POST | `/api/projects` | `{name, source_type, github_url, files[]}` | Create project |
| DELETE | `/api/projects/<id>` | - | Delete project |
| POST | `/api/projects/<id>/start` | - | Start bot process |
| POST | `/api/projects/<id>/stop` | - | Stop bot process |
| POST | `/api/projects/<id>/restart` | - | Restart bot process |
| GET | `/api/projects/<id>/status` | - | Get bot status + uptime |
| GET | `/api/projects/<id>/logs` | `?lines=100` | Get bot logs |
| DELETE | `/api/projects/<id>/logs` | - | Clear bot logs |
| GET | `/api/projects/<id>/files` | - | List project files |
| GET | `/api/projects/<id>/files/<path>` | - | Read file content |
| PUT | `/api/projects/<id>/files/<path>` | `{content}` | Save file content |
| POST | `/api/projects/<id>/files/upload` | `multipart/form-data` | Upload file |
| GET | `/api/projects/<id>/download` | - | Download project as .zip |
| POST | `/api/projects/<id>/env` | `{key, value}` | Update .env variable |
| GET | `/api/projects/<id>/env` | - | Get all .env variables |
| POST | `/api/settings` | `{key, value}` | Update setting |
| GET | `/api/settings` | - | Get all settings |
| POST | `/api/popup/dismiss` | `{show_again: bool}` | Dismiss popup |

---

## 5. Backend Module Design

### 5.1 `app.py` - Main Application

```
app.py
├── Flask app initialization
├── Session config (permanent_session_lifetime)
├── Before request hooks
│   └── check_first_visit() → popup logic
├── Page routes (HTML rendering)
├── API routes (JSON responses)
├── Error handlers (404, 500)
├── App startup
│   ├── Create directories (projects/, uploads/)
│   ├── Initialize database
│   └── Start stats collection thread
└── Run on port 5000
```

### 5.2 `database.py` - Database Operations

```python
# Functions:
init_db()                          # Create tables if not exist
get_all_projects()                 # SELECT * FROM projects
get_project(id)                    # SELECT * FROM projects WHERE id=?
create_project(data)               # INSERT INTO projects
update_project(id, data)           # UPDATE projects SET ...
delete_project(id)                 # DELETE FROM projects WHERE id=?
update_project_status(id, status)  # UPDATE status + timestamps
get_setting(key)                   # SELECT value FROM settings WHERE key=?
set_setting(key, value)            # INSERT OR REPLACE INTO settings
```

### 5.3 `process_manager.py` - Bot Process Management

```python
# Functions:
start_bot(project_id)              # Launch subprocess, track PID
stop_bot(project_id)               # Kill process group
restart_bot(project_id)            # Stop → wait → start
is_running(pid)                    # Check if process alive
get_uptime(start_time)             # Calculate uptime string
capture_output(project_id, proc)   # Thread: capture stdout/stderr to log file

# Internal:
running_processes = {}             # {project_id: subprocess.Popen}
file_start_times = {}              # {project_id: timestamp}
```

**Start Bot Implementation:**
```python
def start_bot(project_id):
    project = get_project(project_id)
    user_dir = f"projects/{project['name']}"
    main_file = f"{user_dir}/{project['main_file']}"

    # Kill existing process if running
    if project_id in running_processes:
        stop_bot(project_id)

    # Determine runtime command
    if project['runtime'] == 'python':
        cmd = ['python3', '-u', main_file]
    elif project['runtime'] == 'node':
        cmd = ['node', main_file]

    # Set environment
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'

    # Load .env file if exists
    env_file = os.path.join(user_dir, '.env')
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env[key] = value

    # Launch subprocess
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=user_dir,
        start_new_session=True     # Isolate process group
    )

    # Track
    running_processes[project_id] = proc
    file_start_times[project_id] = time.time()

    # Update database
    update_project_status(project_id, 'running', pid=proc.pid)

    # Start log capture thread
    log_file = os.path.join(user_dir, '.logs', 'output.log')
    threading.Thread(
        target=capture_output,
        args=(project_id, proc, log_file),
        daemon=True
    ).start()
```

**Stop Bot Implementation:**
```python
def stop_bot(project_id):
    if project_id in running_processes:
        proc = running_processes[project_id]
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except:
            try:
                proc.kill()
            except:
                pass

        running_processes.pop(project_id, None)
        file_start_times.pop(project_id, None)

        update_project_status(project_id, 'stopped')
```

### 5.4 `github_handler.py` - GitHub Integration

```python
# Functions:
clone_repo(url, target_dir)        # git clone into target directory
pull_repo(project_dir)             # git pull latest changes
detect_runtime(project_dir)        # Check for requirements.txt vs package.json
detect_main_file(project_dir)      # Find main.py, bot.py, index.js etc.
```

**Clone Implementation:**
```python
def clone_repo(url, target_dir):
    # Validate URL
    if not url.startswith(('https://github.com/', 'git@github.com:')):
        raise ValueError("Invalid GitHub URL")

    # Clone
    result = subprocess.run(
        ['git', 'clone', url, target_dir],
        capture_output=True, text=True, timeout=120
    )

    if result.returncode != 0:
        raise Exception(f"Clone failed: {result.stderr}")

    return True
```

### 5.5 `auto_installer.py` - Dependency Installer

```python
# Functions:
detect_and_install(project_dir, runtime)   # Main entry point
install_python_deps(project_dir)           # pip install -r requirements.txt
install_node_deps(project_dir)             # npm install
parse_requirements(project_dir)            # Read requirements.txt
parse_package_json(project_dir)            # Read package.json
```

**Python Install Implementation:**
```python
def install_python_deps(project_dir):
    req_file = os.path.join(project_dir, 'requirements.txt')
    venv_dir = os.path.join(project_dir, '.venv')

    if not os.path.exists(req_file):
        return {"status": "no_requirements"}

    # Install to local target directory (no venv needed in Termux)
    result = subprocess.run(
        ['pip', 'install', '-r', req_file,
         '--target', os.path.join(project_dir, 'libs'),
         '--no-cache-dir'],
        capture_output=True, text=True, timeout=300
    )

    if result.returncode != 0:
        raise Exception(f"Install failed: {result.stderr}")

    return {"status": "success"}
```

---

## 6. Frontend Architecture

### 6.1 Base Template (`base.html`)

```html
<!-- CDN Dependencies -->
Tailwind CSS (play CDN)
Font Awesome 6
Chart.js (for stats)
CodeMirror 6 (for editor)
Prism.js (for syntax highlighting in logs)

<!-- Layout -->
<header>  → Logo + Status + Theme Toggle
<nav>     → Dashboard | Create | Settings
<main>    → {% block content %}{% endblock %}
<footer>  → OXYCODE AI + Telegram Link

<!-- Scripts -->
static/js/app.js
{% block scripts %}{% endblock %}
```

### 6.2 Dashboard (`dashboard.html`)

```
┌─ Stats Bar (CPU, RAM, Active Bots) ─────────────┐
├──────────────────────────────────────────────────┤
│ [+ Create Project]                    [🔍 Search]│
├──────────────────────────────────────────────────┤
│ ┌─ Project Card 1 ─────────────────────────────┐ │
│ │ Name: My Telegram Bot          Status: ● Run │ │
│ │ GitHub: github.com/user/repo                  │ │
│ │ [▶] [⏹] [🔄] [📝] [📋] [🗑]                  │ │
│ └──────────────────────────────────────────────┘ │
│ ┌─ Project Card 2 ─────────────────────────────┐ │
│ │ Name: Discord Helper           Status: ● Stop│ │
│ │ [▶] [⏹] [🔄] [📝] [📋] [🗑]                  │ │
│ └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

### 6.3 File Editor (`editor.html`)

```
┌─ Toolbar ────────────────────────────────────────┐
│ [← Back]   main.py                  [💾 Save]    │
├──────────────────────────────────────────────────┤
│ ┌─ CodeMirror Editor ──────────────────────────┐ │
│ │ 1 │ import telebot                           │ │
│ 2 │ bot = telebot.TeleBot("TOKEN")            │ │
│ 3 │                                            │ │
│ 4 │ @bot.message_handler(func=lambda m: True)  │ │
│ 5 │ def handle(message):                       │ │
│ 6 │     bot.reply_to(message, "Hello!")        │ │
│ 7 │                                            │ │
│ 8 │ bot.polling()                              │ │
│ └──────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────┤
│ Ln 8, Col 1  │  45 words  │  Python  │  UTF-8   │
└──────────────────────────────────────────────────┘
```

### 6.4 Live Logs (`logs.html`)

```
┌─ Toolbar ────────────────────────────────────────┐
│ [← Back]   Bot Logs          [🗑 Clear] [⬇️ Save]│
├──────────────────────────────────────────────────┤
│ ┌─ Log Output ─────────────────────────────────┐ │
│ │ [12:00:01] 🟢 Starting bot...                │ │
│ │ [12:00:02] ✅ Connected to Telegram API      │ │
│ │ [12:00:05] 📨 Update received                │ │
│ │ [12:00:05] 📤 Reply sent to user 123456      │ │
│ │ [12:01:30] ⚠️ Flood control: waiting 2s      │ │
│ │ [12:02:00] 📨 Update received                │ │
│ │                                              │ │
│ │ (auto-scroll ↓)                              │ │
│ └──────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────┤
│ Status: ● Running  │  Uptime: 2h 15m 30s        │
└──────────────────────────────────────────────────┘
```

---

## 7. Configuration (`config.py`)

```python
# App Config
APP_NAME = "OXYCODE BOT HOST"
APP_VERSION = "1.0.0"
SECRET_KEY = "oxycode-bot-host-secret-key-change-me"
PORT = 5000
HOST = "0.0.0.0"     # Accessible from phone browser

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
DB_FILE = os.path.join(BASE_DIR, "bot_host.db")

# Limits
MAX_PROJECTS = 10
MAX_PROJECT_SIZE_MB = 100
MAX_TOTAL_STORAGE_MB = 500
MAX_LOG_SIZE_KB = 50
MAX_CONCURRENT_BOTS = 10

# Process
PYTHON_CMD = "python3"
NODE_CMD = "node"
LOG_CAPTURE_INTERVAL = 0.5    # seconds

# Telegram Popup
TELEGRAM_CHANNEL = "https://t.me/OXYCODEAI"
TELEGRAM_CHANNEL_NAME = "@OXYCODEAI"

# Supported file extensions for editor
EDITABLE_EXTENSIONS = [
    '.py', '.js', '.json', '.html', '.css',
    '.yml', '.yaml', '.env', '.md', '.txt',
    '.toml', '.cfg', '.ini', '.sh'
]

# Main file detection order
PYTHON_MAIN_FILES = ['main.py', 'bot.py', 'app.py', 'run.py', 'start.py']
NODE_MAIN_FILES = ['index.js', 'bot.js', 'app.js', 'main.js', 'server.js']
```

---

## 8. Startup Script (`start.sh`)

```bash
#!/bin/bash
# OXYCODE BOT HOST - Termux Startup Script

echo "👾 OXYCODE BOT HOST v1.0"
echo "========================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Installing..."
    pkg install python -y
fi

# Check pip packages
echo "📦 Checking dependencies..."
pip install flask requests 2>/dev/null

# Create directories
mkdir -p projects uploads

# Start server
echo ""
echo "🚀 Starting OXYCODE BOT HOST..."
echo "📱 Open in browser: http://localhost:5000"
echo "📱 Or from another device: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 app.py
```

---

## 9. Error Handling Strategy

| Error Type | Handling |
|-----------|----------|
| Bot crash | Log error, update status to 'error', optional auto-restart |
| Port in use | Try next port (5001, 5002...) |
| Git clone fail | Show error message, suggest checking URL |
| pip install fail | Show error log, allow manual retry |
| File not found | Show 404 page with project list link |
| Database locked | Retry with 100ms delay (max 3 retries) |
| Process kill fail | Force kill with SIGKILL, cleanup tracking |
| Disk full | Block new uploads, show warning |

---

## 10. Security Considerations

| Risk | Mitigation |
|------|-----------|
| Remote code execution | Only localhost access (no remote) |
| Path traversal | Validate all file paths, sanitize input |
| Command injection | Use subprocess with list args (no shell=True) |
| XSS | Escape all user input in templates |
| CSRF | Flask session-based protection |
| Disk abuse | Storage limits per project |
| Process abuse | Max concurrent processes limit |
| GitHub token leak | Store in .env, never log or display |

---

## 11. Performance Optimization

| Area | Strategy |
|------|----------|
| Log reading | Read last N lines only (not full file) |
| Stats caching | Cache CPU/RAM stats for 5 seconds |
| Database | WAL mode for concurrent reads |
| File operations | Lazy loading for large directories |
| Frontend | CDN for all libraries (no local copies) |
| Process cleanup | Auto-clean dead processes on startup |

---

## 12. Testing Plan

| Test Type | Scope |
|-----------|-------|
| Unit tests | database.py functions, config validation |
| Integration tests | API routes, process start/stop |
| Manual tests | Full user flow on Android phone |
| Stress test | 10 concurrent bots running |
| Edge cases | Empty project, missing main.py, bad GitHub URL |

---

## 13. Deployment (Termux)

```bash
# One-time setup on Termux
pkg update && upgrade
pkg install python git

# Clone project
git clone https://github.com/oxycodeai/oxycode-bot-host
cd oxycode-bot-host

# Install dependencies
pip install flask requests

# Run
python3 app.py
# OR
chmod +x start.sh && ./start.sh
```

---

## 14. File Count Summary

| Type | Count | Description |
|------|-------|-------------|
| Python | 5 | app.py, database.py, process_manager.py, github_handler.py, auto_installer.py |
| Config | 2 | config.py, requirements.txt |
| HTML | 6 | base, dashboard, editor, logs, create, env_editor |
| CSS | 1 | style.css |
| JS | 4 | app.js, editor.js, popup.js, logs.js |
| Shell | 1 | start.sh |
| **Total** | **19** | Core files |

---

*Document prepared for OXYCODE BOT HOST v1.0*
*Last updated: August 30, 2026*
