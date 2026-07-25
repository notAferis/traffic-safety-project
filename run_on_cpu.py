import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = ""  # hide any GPU so torch.cuda.is_available() is False
    env["FORCE_CPU"] = "1"  # also skip MPS on Apple Silicon, which CUDA_VISIBLE_DEVICES can't touch
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "ui/main_v2.py"],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
    )
