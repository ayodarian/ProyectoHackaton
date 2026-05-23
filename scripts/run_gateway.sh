#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")/../backend" && pwd)"

echo "[run_gateway] Instalando dependencias..."
pip install -q pyserial pyyaml httpx websockets 2>/dev/null || true

echo "[run_gateway] Iniciando Serial Gateway..."
cd "$DIR"
PYTHONPATH="$DIR:$PYTHONPATH" python3 serial_gateway/gateway.py
