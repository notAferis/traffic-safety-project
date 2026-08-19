import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "ui/main.py"],
        cwd=PROJECT_ROOT,
        check=True,
    )
