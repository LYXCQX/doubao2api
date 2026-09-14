#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "==============================================================="
echo "  Doubao 2API - OpenAI Compatible Proxy"
echo "  Address:      http://127.0.0.1:9090"
echo "  Admin Panel:  http://127.0.0.1:9090/admin"
echo "  OpenAI API:   http://127.0.0.1:9090/v1"
echo "==============================================================="

if [ -f ".venv/bin/python" ]; then
    .venv/bin/python -m doubao2api
elif [ -f "venv/bin/python" ]; then
    venv/bin/python -m doubao2api
else
    python3 -m doubao2api
fi
