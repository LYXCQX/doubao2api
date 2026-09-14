#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "==============================================================="
echo "  Doubao 2API - OpenAI Compatible Proxy"
echo "  Address:      http://127.0.0.1:9090"
echo "  Admin Panel:  http://127.0.0.1:9090/admin"
echo "  OpenAI API:   http://127.0.0.1:9090/v1"
echo "==============================================================="

PY_CMD=""
if [ -f ".venv/bin/python" ]; then
    PY_CMD=".venv/bin/python"
elif [ -f "venv/bin/python" ]; then
    PY_CMD="venv/bin/python"
elif command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "[Error] Python not found. Please install Python 3.10+."
    exit 1
fi

# Check dependencies
if ! $PY_CMD -c "import fastapi, playwright, uvicorn" &>/dev/null; then
    echo "[Info] Missing dependencies. Installing requirements..."
    $PY_CMD -m pip install -r requirements.txt
    echo "[Info] Installing Playwright Chromium browser..."
    $PY_CMD -m playwright install chromium
fi

export DOUBAO_HEADLESS="${DOUBAO_HEADLESS:-auto}"
export DOUBAO_AUTO_DELETE_CONV="${DOUBAO_AUTO_DELETE_CONV:-true}"

exec $PY_CMD -m doubao2api
