# OXYCODE BOT HOST 👾

Lightweight bot hosting platform for Termux. Manage, monitor, and run Telegram and Discord bots from your phone.

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat-square&logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Features

- **One-Click Hosting** - Start/stop/restart bots with a single tap
- **GitHub Import** - Clone any repo, auto-detect runtime and dependencies
- **File Editor** - Built-in code editor with syntax highlighting (CodeMirror)
- **Live Logs** - Real-time log viewer with auto-refresh
- **Environment Editor** - Manage .env variables easily
- **System Stats** - Monitor CPU, RAM, and disk usage
- **Mobile-First UI** - Dark theme, works great on phones
- **Python + Node.js** - Supports both runtimes

---

## Installation

**First Time Setup (run once):**

```
pkg update -y && pkg install git python -y && git clone https://github.com/oxycodeai/oxycode-bot-host.git && cd oxycode-bot-host && bash start.sh
```

**After Phone Off / Quick Start:**

```
cd ~/oxycode-bot-host && bash start.sh
```

Then open `http://127.0.0.1:5000` in your browser.

---

## How It Works

1. Install [Termux](https://f-droid.org/en/packages/com.termux/) from F-Droid
2. Paste the **First Time Setup** command in Termux
3. Wait for installation to complete
4. Open `http://127.0.0.1:5000` in your browser
5. Create bots, import from GitHub, edit files, view logs

---

## Usage

### Create a Bot

1. Click **+ New Bot** on the dashboard
2. Enter a name (letters, numbers, `-`, `_`)
3. Optionally paste a GitHub repository URL
4. Click **Create Bot**

### Import from GitHub

1. Paste any public GitHub repo URL
2. Runtime (Python/Node.js) is auto-detected
3. Dependencies from `requirements.txt` or `package.json` are installed automatically

### Edit Files

1. Click **Edit** on any bot card
2. Select a file from the sidebar
3. Edit with syntax highlighting
4. Press `Ctrl+S` or click **Save**

### View Logs

1. Click **Logs** on any bot card
2. Logs auto-refresh every 3 seconds
3. Toggle auto-scroll on/off

---

## Configuration

Edit `config.py` to change settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `PORT` | 5000 | Server port |
| `HOST` | 127.0.0.1 | Bind address |
| `MAX_BOTS` | 50 | Maximum number of bots |
| `CLONE_TIMEOUT` | 120 | Git clone timeout (seconds) |

---

## Tech Stack

- **Backend:** Python, Flask, SQLite
- **Frontend:** Tailwind CSS, CodeMirror, Vanilla JS
- **Process:** subprocess, psutil

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Built by [OXYCODE AI](https://t.me/OXYCODEAI)
