#!/usr/bin/env python3
import socket
import time
import requests


def is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def verify():
    if not is_port_open(4111):
        print("Servidor não está rodando na porta 4111.")
        return 1

    base = "http://127.0.0.1:4111"
    r = requests.get(f"{base}/healthz", timeout=5)
    assert r.status_code == 200 and r.json().get("ok") is True

    r = requests.post(f"{base}/api/buscar", json={"q": "presente pra mae jardim", "fresh": True}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["n_produtos"] == 120
    print("Offline OK")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(verify())
