import os

APP_NAME = "OXYCODE BOT HOST"
APP_VERSION = "1.0.0"
PORT = 5000
HOST = "127.0.0.1"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
DB_PATH = os.path.join(BASE_DIR, "bot_host.db")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

TELEGRAM_LINK = "https://t.me/OXYCODEAI"
TELEGRAM_CHANNEL = "@OXYCODEAI"

MAX_BOTS = 50
MAX_UPLOAD_SIZE_MB = 500
CLONE_TIMEOUT = 120

PYTHON_EXT = (".py",)
NODE_EXT = (".js", ".mjs", ".ts")
ENV_FILE = ".env"

ALLOWED_EDIT_EXT = (
    ".py", ".js", ".ts", ".json", ".html", ".css",
    ".yml", ".yaml", ".md", ".txt", ".env", ".sh",
    ".toml", ".cfg", ".ini", ".conf"
)

RUNTIME_PYTHON = "python"
RUNTIME_NODE = "node"
