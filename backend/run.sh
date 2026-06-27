#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-dev}"

echo "Stopping any existing booking-agent workers..."
pkill -9 -f "src.agent dev" 2>/dev/null || true
pkill -9 -f "src.agent console" 2>/dev/null || true
pkill -9 -f "src.agent start" 2>/dev/null || true
sleep 1

echo "Starting one worker: src.agent $MODE"
exec .venv/bin/python -m src.agent "$MODE"
