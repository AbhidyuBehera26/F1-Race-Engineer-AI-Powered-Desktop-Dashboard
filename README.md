# F1 Race Engineer — AI-Powered Desktop Dashboard

> AI-powered F1 Race Engineer desktop dashboard. Built with PyQt6 and local Llama 3.1 via Ollama — no cloud, no cost, no latency. AI chat uses live weather tool-calling and local knowledge base search to deliver real engineering data. Renders real 2024 Belgian GP telemetry via FastF1 and Matplotlib. Fully Dockerised stack with OpenAI GPT-4o fallback.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6+-green?style=flat-square)
![Ollama](https://img.shields.io/badge/Ollama-Llama_3.1-orange?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Containerised-2496ED?style=flat-square&logo=docker)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## Overview

A professional desktop application that replaces a Jupyter/Colab notebook with a native **PyQt6 dashboard**. The left panel hosts an AI chat powered by **Llama 3.1 running locally via Ollama**. The right panel renders real **2024 Belgian GP telemetry** fetched via FastF1 and plotted with Matplotlib — no external sandbox, no latency.

```
┌──────────────────────────┬──────────────────────────────────┐
│     CHIEF RACE ENGINEER  │  LIVE TELEMETRY                  │
│                          │                                  │
│  AI Chat Interface       │  Speed / Throttle / Brake        │
│  • Live weather API      │  2024 Belgian GP — Fastest Lap   │
│  • Knowledge base search │                                  │
│  • Tool-calling loop     │  [Refresh]                       │
│                          │                                  │
│  [ Type message... ]     │                                  │
└──────────────────────────┴──────────────────────────────────┘
```

---

## Features

- **Local LLM** — Llama 3.1 8B runs entirely on your GPU via Ollama. No API key, no internet after model download.
- **Tool-calling loop** — AI fetches live track weather (Open-Meteo) and searches a local F1 knowledge base before answering.
- **Real telemetry** — FastF1 pulls actual race data from the 2024 Belgian GP. Matplotlib renders it locally in a background thread.
- **Native Qt UI** — Built with PyQt6, dark F1-themed design, animated loading indicators, and quick-start suggestion buttons.
- **OpenAI fallback** — If Ollama is not running, the app automatically switches to GPT-4o.
- **Docker ready** — Full `docker-compose.yml` orchestrates the app + Ollama server as two containers.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop UI | PyQt6 |
| Local LLM | Ollama + Llama 3.1 8B |
| Cloud LLM fallback | OpenAI GPT-4o |
| Telemetry data | FastF1 |
| Graph rendering | Matplotlib |
| Weather API | Open-Meteo (free, no key) |
| Containerisation | Docker + Docker Compose |

---

## Quick Start

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com) installed

### 1. Clone the repo
```bash
git clone https://github.com/AbhidyuBehera26/F1-Race-Engineer-AI-Powered-Desktop-Dashboard.git
cd F1-Race-Engineer-AI-Powered-Desktop-Dashboard
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Download the AI model (one-time, ~5GB)
```bash
ollama pull llama3.1:8b
```

### 4. Run the app
```bash
python run.py
```

> **Note:** On first launch, FastF1 will download ~50MB of race session data and cache it locally. Subsequent launches load from cache instantly.

---

## 🔄 OpenAI Fallback

If you prefer GPT-4o instead of running Ollama locally:

1. Create a file called `openAI_key.txt` in the project root
2. Paste your OpenAI API key inside it
3. Run the app without starting Ollama — it detects automatically

> `openAI_key.txt` is listed in `.gitignore` and will never be committed to GitHub.

---

## 🐳 Docker Deployment

```bash
# Start both containers (app + Ollama LLM server)
docker-compose up

# Stop
docker-compose down
```

Docker Compose will:
- Start an **Ollama** container with the model weights stored in a named volume
- Build and start the **F1 Race Engineer** app container
- Link them via Docker's internal network

> **Windows users:** Native `python run.py` is recommended for development. Docker is configured for Linux/cloud deployment.

---

## roject Structure

```
├── run.py                    ← Entry point: python run.py
├── requirements.txt          ← Python dependencies
├── Dockerfile                ← Container image definition
├── docker-compose.yml        ← Multi-container orchestration
├── Gen_AI.ipynb              ← Original prototype notebook
└── app/
    ├── main.py               ← QApplication, dark theme stylesheet
    ├── knowledge_base.txt    ← Local F1 engineering reference
    ├── backend/
    │   ├── engineer.py       ← AI engine, Ollama/OpenAI, tool-calling loop
    │   ├── telemetry.py      ← FastF1 fetch + Matplotlib chart generation
    │   └── weather.py        ← Open-Meteo live weather API
    └── ui/
        ├── dashboard.py      ← QMainWindow + QSplitter layout
        ├── chat_panel.py     ← Chat bubbles, loading animation, input bar
        └── telemetry_panel.py← QLabel + QPixmap graph rendering
```

---

## Example Queries

| Query | What the AI does |
|---|---|
| *"What tyres for Spa today?"* | Calls weather API → checks track temp → recommends compound + PSI |
| *"Best aero setup for Monza?"* | Searches knowledge base → returns wing angles in degrees |
| *"Analyse the brake zones"* | Searches KB → returns specific brake board distances |
| *"Should I undercut my rival?"* | Uses strategy rules → gives lap delta calculation |

---

## 📄 License

MIT License — free to use, modify, and distribute.
