# Runs the Streamlit dashboard (ui/main.py) in a container.
#
# IMPORTANT — no GPU/MPS acceleration inside the container: Docker Desktop on macOS
# (Apple Silicon included) does not pass Metal through to Linux containers, so DETR
# will run on CPU here regardless of the host being an M2 Pro. If you want to actually
# benchmark MPS speed, run the project natively on macOS via `uv sync` instead (see
# USAGE.md) — use this Dockerfile for a convenient, reproducible way to run/demo the
# dashboard, not for a speed test.
#
# The verifier LLM (qwen2.5vl:3b) is expected to run via Ollama on the HOST machine,
# not inside this container — point OLLAMA_HOST at the host from `docker run` (see the
# accompanying README/USAGE note for the exact value on macOS).

FROM python:3.13-slim

# libgl1/libglib2.0-0: required at runtime by opencv-python (cv2) even in headless use.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first, separately from app code, so editing source files
# doesn't invalidate this (slow) layer on rebuild.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-install-project

# Now bring in the actual application code.
COPY ui/ ui/
COPY agentic/ agentic/
COPY .streamlit/ .streamlit/
RUN uv sync --locked

ENV PATH="/app/.venv/bin:${PATH}"

# Never resolves to true inside a container, but keeps startup deterministic
# either way instead of silently probing for a GPU/MPS that can't be reached.
ENV FORCE_CPU=1

EXPOSE 8501

CMD ["streamlit", "run", "ui/main.py", "--server.address=0.0.0.0", "--server.port=8501"]

