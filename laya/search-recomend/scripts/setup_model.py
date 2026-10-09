#!/usr/bin/env python3
import sys
import subprocess
import importlib.util
from pathlib import Path


def check_laya():
    spec = importlib.util.find_spec("laya")
    if spec is None:
        print("LAYA package not installed.")
        print("Install with: pip install laya")
        return False
    print("LAYA package found.")
    return True


def download_model(checkpoint: str = "laya-multilingual"):
    try:
        import laya
        print(f"Downloading {checkpoint}...")
        laya.download(checkpoint)
        print("Model downloaded.")
        return True
    except Exception as e:
        print(f"Failed to download via laya package: {e}")
        return False


def main():
    print("Verificando LAYA...")
    if check_laya():
        print("Modelo disponível localmente.")
        return 0
    print("Modelo não encontrado.")
    print("Tentando baixar...")
    if download_model():
        return 0
    print("Aviso: LAYA não disponível. A aplicação usará busca por similaridade local.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
