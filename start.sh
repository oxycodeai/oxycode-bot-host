#!/data/data/com.termux/files/usr/bin/bash

echo ""
echo "  ██████╗ ██████╗  ██████╗ ██╗  ██╗██╗███████╗███████╗"
echo "  ██╔═══██╗██╔══██╗██╔═══██╗╚██╗██╔╝██║██╔════╝██╔════╝"
echo "  ██║   ██║██████╔╝██║   ██║ ╚███╔╝ ██║█████╗  ███████╗"
echo "  ██║   ██║██╔══██╗██║   ██║ ██╔██╗ ██║██╔══╝  ╚════██║"
echo "  ╚██████╔╝██║  ██║╚██████╔╝██╔╝ ██╗██║███████╗███████║"
echo "   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝"
echo ""
echo "  BOT HOST 👾 v1.0.0"
echo "  Lightweight bot hosting for Termux"
echo ""

cd "$(dirname "$0")"

if ! command -v python &> /dev/null; then
    echo "[!] Python not found. Installing..."
    pkg update -y && pkg install python -y
fi

if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment..."
    python -m venv venv
fi

source venv/bin/activate

if [ ! -f "venv/.deps_installed" ]; then
    echo "[*] Installing dependencies..."
    pip install -r requirements.txt
    touch venv/.deps_installed
fi

mkdir -p projects logs

echo "[*] Starting OXYCODE BOT HOST on http://127.0.0.1:5000"
echo "[*] Press Ctrl+C to stop"
echo ""

python app.py
