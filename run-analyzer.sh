#!/bin/bash

echo "╭───────────────────────────────────────"
echo "│  claude code log analyzer"
echo "│  starting server..."
echo "╰───────────────────────────────────────"
echo ""

export PYTHONPATH="${PYTHONPATH}:$(pwd)"

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
