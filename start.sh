#!/data/data/com.termux/files/usr/bin/bash

echo ""
echo "  ██████╗ ██████╗  ██████╗ ██╗  ██╗██╗███████╗███████╗"
echo "  ██╔═══██╗██╔══██╗██╔═══██╗╚██╗██╔╝██║██╔════╝██╔════╝"
echo "  ██║   ██║██████╔╝██║   ██║ ╚███╔╝ ██║█████╗  ███████╗"
echo "  ██║   ██║██╔══██╗██║   ██║ ██╔██╗ ██║██╔══╝  ╚════██║"
echo "  ╚██████╔╝██║  ██║╚██████╔╝██╔╝ ██╗██║███████╗███████║"
echo "   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝"
echo ""
echo "  BOT HOST v2.1.0"
echo ""

pip install flask requests psutil 2>/dev/null

mkdir -p projects logs

echo ""
echo "[*] Starting on http://127.0.0.1:5000"
echo ""

python app.py
