# ── F1 Race Engineer — Docker Container Definition ──────────────────────────
#
# A Dockerfile is a recipe for building a container image.
# Think of it as a script that sets up a fresh Linux machine from scratch,
# installs all dependencies, and configures how to run your application.
#
# When you run: docker build -t f1-engineer .
# Docker reads this file top-to-bottom and creates a layered image.
# Each instruction (FROM, RUN, COPY, etc.) creates a new layer.
# Layers are cached — if nothing changes, Docker reuses the cached layer (fast rebuilds).
#
# Why Docker?
# "Works on my machine" is not acceptable in production.
# Docker packages your app + ALL its dependencies into a single portable unit.
# Anyone with Docker can run your app with: docker-compose up
# No Python version mismatches, no missing libraries, no environment variables forgotten.

# ── Base Image ──
# We start FROM an official Python 3.11 image (slim = smaller, no extras)
# This is the foundation layer — like installing an OS.
FROM python:3.11-slim

# ── Maintainer label (metadata) ──
LABEL maintainer="F1 Race Engineer AI"
LABEL description="AI-powered F1 race engineer desktop dashboard"
LABEL version="2.0"

# ── System dependencies ──
# RUN executes a shell command during the build.
# We install system libraries that PyQt6 needs to render a GUI window.
# The && chains commands and \ continues the line (style convention).
# rm -rf /var/lib/apt/lists/* removes the package index cache to keep the image small.
RUN apt-get update && apt-get install -y \
    # Virtual display (allows GUI apps to run without a real monitor)
    xvfb \
    # OpenGL library (PyQt6 needs this for rendering)
    libgl1 \
    # GLib (fundamental Linux system library)
    libglib2.0-0 \
    # X11 keyboard support for Qt
    libxkbcommon-x11-0 \
    # XCB libraries (Qt's low-level Linux display system)
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-shape0 \
    libxcb-cursor0 \
    # Font rendering
    libfontconfig1 \
    && rm -rf /var/lib/lib/apt/lists/*

# ── Working directory ──
# All subsequent commands run from this directory inside the container.
WORKDIR /app

# ── Install Python dependencies ──
# We COPY requirements.txt FIRST (before the app code).
# Why? Docker caches each layer. If only your app code changes (not requirements),
# Docker skips reinstalling pip packages and reuses the cached layer. Much faster!
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application code ──
# Now copy the actual app. This layer changes often, so it's after pip install.
COPY app/ ./app/

# ── Environment variables ──
# DISPLAY tells Qt which display server to connect to.
# When running without a real monitor (headless), we use Xvfb on :99.
ENV DISPLAY=:99
# Tell matplotlib not to try to open a GUI window
ENV MPLBACKEND=Agg
# Ollama server address (overridden in docker-compose to point to the ollama container)
ENV OLLAMA_HOST=http://localhost:11434

# ── Startup command ──
# CMD is what runs when you start the container.
# We start Xvfb (virtual display) then launch the Python app.
# If a real DISPLAY is provided (e.g., from the host via X11 forwarding),
# the app will use that instead.
CMD Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp & \
    sleep 1 && \
    python -m app.main
