"""
Serial Gateway — ESP8266 USB ↔ FastAPI Backend

Reads JSON telemetry from ESP8266 via Serial, forwards to backend REST API.
Connects via WebSocket to receive paro_emergencia commands and relays to device.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import yaml

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("ERROR: pyserial not installed. Run: pip install -r requirements-gateway.txt")
    sys.exit(1)


API_BASE = os.environ.get("API_BASE", "http://localhost:8000")
WS_URL = os.environ.get("WS_URL", "ws://localhost:8000/ws/{torno_id}")
CONFIG_PATH = Path(__file__).parent / "config.yml"


@dataclass
class DeviceConfig:
    port: str
    torno_id: int
    baudrate: int = 115200


@dataclass
class DeviceConnection:
    config: DeviceConfig
    serial: serial.Serial | None = None
    paro_emergencia: bool = False
    http_client: httpx.AsyncClient = field(default_factory=httpx.AsyncClient)
    ws: Any = None
    running: bool = True


def load_config() -> list[DeviceConfig]:
    if not CONFIG_PATH.exists():
        print(f"[gateway] config.yml not found at {CONFIG_PATH}")
        return []
    with open(CONFIG_PATH) as f:
        data = yaml.safe_load(f)
    devices: list[DeviceConfig] = []
    for item in data.get("devices", []):
        devices.append(DeviceConfig(
            port=item["port"],
            torno_id=item["torno_id"],
            baudrate=item.get("baudrate", 115200),
        ))
    return devices


def find_serial_port(hint: str) -> str | None:
    if hint and hint != "auto":
        return hint
    ports = serial.tools.list_ports.comports()
    for p in sorted(ports):
        if "USB" in p.description.upper() or "UART" in p.description.upper():
            return p.device
    return None


async def send_telemetry(conn: DeviceConnection, payload: dict) -> None:
    url = f"{API_BASE}/api/telemetria"
    try:
        vib_total = payload.get("vib_total", 0.0)
        body = {
            "torno_id": conn.config.torno_id,
            "temperatura": payload.get("temperatura", 0.0),
            "vibracion_x": vib_total,
            "vibracion_y": 0.0,
            "vibracion_z": 0.0,
        }
        resp = await conn.http_client.post(url, json=body, timeout=5)
        if resp.status_code not in (200, 201):
            print(f"[t#{conn.config.torno_id}] HTTP {resp.status_code}")
    except Exception as e:
        print(f"[t#{conn.config.torno_id}] HTTP error: {e}")


async def read_serial(conn: DeviceConnection) -> None:
    while conn.running and conn.serial:
        try:
            if conn.serial.in_waiting <= 0:
                await asyncio.sleep(0.05)
                continue
            raw = conn.serial.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").strip()
        except Exception as e:
            print(f"[t#{conn.config.torno_id}] serial read error: {e}")
            await asyncio.sleep(1)
            continue

        if not line:
            continue

        try:
            msg = json.loads(line)
            if not isinstance(msg, dict):
                continue
        except json.JSONDecodeError:
            continue

        msg_type = msg.get("type", "")
        if msg_type == "telemetry":
            asyncio.ensure_future(send_telemetry(conn, msg))
        elif msg_type == "status":
            print(f"[t#{conn.config.torno_id}] status: {msg.get('message', '')}")


async def write_serial(conn: DeviceConnection, command: dict) -> None:
    if not conn.serial:
        return
    try:
        line = json.dumps(command) + "\n"
        conn.serial.write(line.encode("utf-8"))
        print(f"[t#{conn.config.torno_id}] -> {line.strip()}")
    except Exception as e:
        print(f"[t#{conn.config.torno_id}] serial write error: {e}")


async def ws_listener(conn: DeviceConnection) -> None:
    import websockets
    url = WS_URL.replace("{torno_id}", str(conn.config.torno_id))
    while conn.running:
        try:
            async with websockets.connect(url) as ws:
                conn.ws = ws
                print(f"[t#{conn.config.torno_id}] WS connected")
                async for raw in ws:
                    msg = json.loads(raw)
                    if msg.get("type") == "estado":
                        data = msg.get("data", {})
                        paro = data.get("paro_emergencia", False)
                        if paro != conn.paro_emergencia:
                            conn.paro_emergencia = paro
                            cmd = {
                                "type": "command",
                                "action": "paro_emergencia",
                                "value": paro,
                            }
                            await write_serial(conn, cmd)
        except Exception as e:
            print(f"[t#{conn.config.torno_id}] WS error: {e}, reconnecting in 3s")
            conn.ws = None
            await asyncio.sleep(3)


async def open_serial(conn: DeviceConnection) -> bool:
    port = find_serial_port(conn.config.port)
    if not port:
        print(f"[t#{conn.config.torno_id}] no serial port found for {conn.config.port}")
        return False
    try:
        conn.serial = serial.Serial(
            port=port,
            baudrate=conn.config.baudrate,
            timeout=1,
        )
        print(f"[t#{conn.config.torno_id}] opened {port} @ {conn.config.baudrate} baud")
        return True
    except Exception as e:
        print(f"[t#{conn.config.torno_id}] cannot open {port}: {e}")
        return False


async def run_device(conn: DeviceConnection) -> None:
    if not await open_serial(conn):
        return
    tasks = [
        asyncio.create_task(read_serial(conn)),
        asyncio.create_task(ws_listener(conn)),
    ]
    done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    for t in done:
        exc = t.exception()
        if exc:
            print(f"[t#{conn.config.torno_id}] task error: {exc}")
    conn.running = False


async def scan_loop(configs: list[DeviceConfig]) -> None:
    """Periodically re-scan for auto devices that might appear later."""
    known_ports: set[str] = set()
    while True:
        for cfg in configs:
            if cfg.port != "auto":
                continue
            port = find_serial_port("auto")
            if port and port not in known_ports:
                known_ports.add(port)
                conn = DeviceConnection(config=DeviceConfig(
                    port=port, torno_id=cfg.torno_id, baudrate=cfg.baudrate
                ))
                asyncio.ensure_future(run_device(conn))
        await asyncio.sleep(5)


async def main() -> None:
    configs = load_config()
    if not configs:
        print("[gateway] no devices configured in config.yml")
        return

    print(f"[gateway] starting with {len(configs)} device(s)")

    tasks = []
    for cfg in configs:
        if cfg.port == "auto":
            port = find_serial_port("auto")
            if port:
                cfg = DeviceConfig(port=port, torno_id=cfg.torno_id, baudrate=cfg.baudrate)
                conn = DeviceConnection(config=cfg)
                tasks.append(asyncio.create_task(run_device(conn)))
            else:
                print(f"[gateway] auto port for torno #{cfg.torno_id} not found yet, will scan")
        else:
            conn = DeviceConnection(config=cfg)
            tasks.append(asyncio.create_task(run_device(conn)))

    tasks.append(asyncio.create_task(scan_loop(configs)))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[gateway] shutting down")
