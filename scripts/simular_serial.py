"""
Serial Simulator — emulates ESP8266 sending telemetry via virtual serial port.

Creates a pair of virtual serial ports with socat, sends telemetry every 2s,
and listens for paro_emergencia commands.
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
import threading

try:
    import serial
except ImportError:
    print("ERROR: pyserial not installed")
    sys.exit(1)

TORNO_ID = int(os.environ.get("TORNO_ID", "1"))
SERIAL_PORT = os.environ.get("SERIAL_PORT", "/tmp/ttyV0")
BAUDRATE = 115200


def main():
    print(f"[sim-esp8266] starting on {SERIAL_PORT} (torno #{TORNO_ID})")
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

    def reader():
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode("utf-8", errors="replace").strip()
                if line:
                    print(f"[sim-esp8266] <- {line}")
            time.sleep(0.05)

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    step = 0
    while True:
        step += 1
        temp = 25.0 + (step % 50) * 1.5 + random.uniform(-1, 1)
        vib = 0.0 + (step % 50) * 0.1 + random.uniform(-0.1, 0.1)
        temp = min(temp, 100.0)
        vib = min(vib, 5.0)

        payload = {
            "type": "telemetry",
            "torno_id": TORNO_ID,
            "temperatura": round(temp, 1),
            "vib_total": round(vib, 2),
        }
        line = json.dumps(payload) + "\n"
        ser.write(line.encode("utf-8"))
        print(f"[sim-esp8266] -> {line.strip()}")

        time.sleep(2)


if __name__ == "__main__":
    main()
