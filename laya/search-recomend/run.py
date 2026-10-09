import sys
import subprocess
import os
from pathlib import Path


def run():
    root = Path(__file__).resolve().parent
    venv = root / ".venv"
    python = sys.executable

    if not venv.exists():
        print("Criando ambiente virtual...")
        subprocess.run([python, "-m", "venv", str(venv)], check=True)

    pip = venv / "Scripts" / "pip.exe" if sys.platform == "win32" else venv / "bin" / "pip"
    python_venv = venv / "Scripts" / "python.exe" if sys.platform == "win32" else venv / "bin" / "python"

    print("Instalando dependências...")
    subprocess.run([str(pip), "install", "-r", str(root / "requirements.txt")], check=True)

    print("Iniciando aplicação...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    proc = subprocess.Popen([str(python_venv), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "4111"], cwd=str(root), env=env)

    import time
    time.sleep(3)

    url = "http://127.0.0.1:4111"
    print(f"\nAplicação disponível em: {url}\n")

    try:
        if sys.platform == "win32":
            os.startfile(url)
        elif sys.platform == "darwin":
            subprocess.run(["open", url])
        else:
            subprocess.run(["xdg-open", url])
    except Exception:
        pass

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    run()
