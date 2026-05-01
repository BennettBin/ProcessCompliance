from __future__ import annotations

import argparse
import json
import urllib.request
import socket
import subprocess
import sys
from pathlib import Path


def port_in_use(host: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()


def is_backend_health_ok(host: str, port: int) -> bool:
    url = f"http://{host}:{port}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=1.5) as resp:
            if resp.status != 200:
                return False
            body = resp.read().decode("utf-8", errors="ignore")
            payload = json.loads(body)
            return payload.get("status") == "ok"
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Start ProcessCompliance backend safely.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5174)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    try:
        import uvicorn  # noqa: F401
    except Exception:
        print("[start_backend] Missing dependency: uvicorn")
        print("[start_backend] Install with:")
        print("  pip install fastapi uvicorn python-multipart")
        return 1

    if port_in_use(args.host, args.port):
        if is_backend_health_ok(args.host, args.port):
            print(f"[start_backend] Backend already running at http://{args.host}:{args.port}")
            return 0
        print(
            f"[start_backend] Port {args.port} is occupied by another service. "
            f"Please free it, or use a different backend port."
        )
        return 1

    root = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if args.reload:
        cmd.append("--reload")

    print(f"[start_backend] Starting backend at http://{args.host}:{args.port}")
    subprocess.Popen(cmd, cwd=str(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
