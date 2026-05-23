#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "[run_test_serial] Verificando socat..."
if ! command -v socat &>/dev/null; then
    echo "ERROR: socat no instalado. Instalar con: sudo apt install socat"
    exit 1
fi

PORTA=/tmp/ttyV0
PORTB=/tmp/ttyV1

# Cleanup previous
rm -f "$PORTA" "$PORTB" 2>/dev/null || true

# Create virtual serial pair
socat PTY,link="$PORTA",raw,echo=0 PTY,link="$PORTB",raw,echo=0 &
SOCAT_PID=$!
sleep 1

echo "[run_test_serial] Virtual ports: $PORTA <-> $PORTB"

# Update config.yml to use the virtual port
cat > "$DIR/backend/serial_gateway/config.yml" <<YAML
devices:
  - port: $PORTB
    torno_id: 1
    baudrate: 115200
YAML

cleanup() {
    echo "[run_test_serial] cleaning up..."
    kill $SOCAT_PID 2>/dev/null || true
    rm -f "$PORTA" "$PORTB" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

echo "[run_test_serial] Iniciando simulador serial..."
python3 "$DIR/scripts/simular_serial.py" &
SIM_PID=$!

echo "[run_test_serial] Iniciando gateway..."
cd "$DIR/backend"
PYTHONPATH="$DIR/backend:$PYTHONPATH" python3 serial_gateway/gateway.py &
GATEWAY_PID=$!

wait
