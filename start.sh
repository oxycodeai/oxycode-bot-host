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
echo ""

pkg update -y > /dev/null 2>&1
pkg install python -y > /dev/null 2>&1

pip install flask requests psutil > /dev/null 2>&1

mkdir -p projects logs

echo "[*] Starting on http://127.0.0.1:5000"
echo ""

python app.py
