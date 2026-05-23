#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=============================================="
echo "  SISTEMA IIoT - TORNO CNC"
echo "  Arranque completo"
echo "=============================================="
echo ""

# 1. Backend
echo "[1/3] Iniciando Backend (FastAPI) en puerto 8000..."
cd "$DIR/backend"
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
sleep 3
echo "  ✓ Backend PID $BACKEND_PID"

# 2. Gateway
echo "[2/3] Iniciando Serial Gateway..."
cd "$DIR/backend"
nohup python3 serial_gateway/gateway.py > /tmp/gateway.log 2>&1 &
GATEWAY_PID=$!
sleep 2
echo "  ✓ Gateway PID $GATEWAY_PID"

# 3. Frontend
echo "[3/3] Iniciando Frontend en puerto 3000..."
cd "$DIR/frontend"
nohup python3 -m http.server 3000 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 1
echo "  ✓ Frontend PID $FRONTEND_PID"

echo ""
echo "=============================================="
echo "  Todo iniciado:"
echo "  - Backend:  http://localhost:8000"
echo "  - Frontend: http://localhost:3000"
echo "  - Gateway:  leyendo serial..."
echo ""
echo "  Para ver logs:"
echo "    tail -f /tmp/backend.log"
echo "    tail -f /tmp/gateway.log"
echo "=============================================="
