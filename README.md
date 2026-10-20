# F1 Race Engineer — AI-Powered Desktop Dashboard

> An authentic, desktop-class Formula 1 Race Engineer dashboard and telemetry analysis suite. Built with **PyQt6**, **FastF1**, **OpenF1**, and an offline **Llama 3.1 8B** model via **Ollama**. Features live circuit weather integration, deterministic Python guardrails against AI hallucinations, and real-time fastest lap sensor telemetry.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6+-green?style=flat-square)
![Ollama](https://img.shields.io/badge/Ollama-Llama_3.1-orange?style=flat-square)
![FastF1](https://img.shields.io/badge/Data-FastF1%20%26%20OpenF1-red?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## Overview

Most motorsport AI tools are either simple API wrappers around ChatGPT or web prototypes that suffer from hallucinated setups and fake telemetry. 

The **F1 Race Engineer Dashboard** is an authentic, local-first engineering desktop application that bridges raw sensor telemetry with context-aware race engineer coaching:
* **Left Panel (AI Race Engineer):** A local 8B LLM running on your machine with tool-calling capabilities. It queries circuit setup notes, fetches live weather, and calculates temperature-adjusted tyre pressures directly in Python.
* **Right Panel (Fastest Lap Telemetry):** Renders synchronized Speed, Throttle, and stepped Brake traces from real 2024 Belgian Grand Prix fastest lap telemetry (Sergio Perez, Red Bull RB20, 1:44.701).

```text
┌───────────────────────────────────────┬────────────────────────────────────────┐
│         CHIEF RACE ENGINEER           │        FASTEST LAP TELEMETRY           │
├───────────────────────────────────────┼────────────────────────────────────────┤
│ • Offline Llama 3.1 8B (via Ollama)   │ • Real 2024 Belgian GP Lap 44 Telemetry│
│ • Circuit Guardrails (Zero Guessing)  │ • Speed trace (74 to 319 km/h)         │
│ • Deterministic Pressure Calculations │ • Throttle trace & partial lifts       │
│ • Open-Meteo Live Weather Integration │ • Authentic binary Brake steps (0/100) │
│                                       │                                        │
│ [ Tyres for Spa? ] [ Brake zones ]    │ [ Refresh ]                            │
└───────────────────────────────────────┴────────────────────────────────────────┘
```

---

## Key Engineering & Research Findings

This project moved beyond surface-level AI wrappers by benchmarking small language models and validating public telemetry feeds against real-world FIA data:

### 1. Telemetry Sensor Constraints: Public Streams vs. Synthetic Data
* **The Reality:** Public Formula 1 telemetry streams (FastF1 / FIA live timing) **do not broadcast continuous hydraulic brake pressure** (bar/PSI) due to team IP secrecy. The public brake sensor is strictly a **binary flag: `0` (off) or `100` (on)**.
* **Authentic Implementation:** This dashboard renders genuine stepped square-wave telemetry across the 8 distinct braking zones at Spa-Francorchamps, highlighting the Bus Stop chicane as the heaviest braking zone ($\Delta v = 219\text{ km/h}$, dropping from 293 km/h to 74 km/h over ~100 meters).

### 2. Strategy Stint Variance: The "Laps-Per-Tyre" Fallacy
* **The Assumption:** Generic engineering references claim that Hard tyres last a single fixed window (e.g. *"25 to 34 laps"*).
* **The Data:** Using the included [`stints.py`](stints.py) pipeline to process all 58 driver stints from the 2024 Belgian GP revealed that Hard tyre stints actually spanned from **5 to 34 laps**, with a **median of only 19 laps**:
  ```text
  Compound   Stints   Min    Median   Mean     Max   
  ------------------------------------------------
  HARD       27       5      19       19.6     34    
  MEDIUM     27       1      11       11.3     24    
  SOFT       4        1      1        3.0      8     
  ```
* **Takeaway:** Tyre wear is driven by **strategic intent**, not compound alone. 2-stop drivers ran aggressive 14–19 lap Hard stints, while only 1-stop strategies (e.g. George Russell) nursed Hards past 27 laps.

### 3. AI Guardrail Engineering: Deterministic Code vs. Prompt Hope
* **The Problem:** Small local language models (8B parameters) frequently fail at multi-tool orchestration, make arithmetic mistakes, and leak generic data when faced with user typos (e.g. `"Typres"`).
* **The Solution:** Moved domain validation, live weather fetching, and tyre pressure physics directly into **deterministic Python code**. If a circuit lacks documented tyres (like Monza or Silverstone), the code immediately returns a strict *"not documented"* notice, eliminating hallucinated compounds.

---

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| **Desktop UI** | PyQt6 | Native desktop GUI with high-DPI scaling and asynchronous event loop |
| **Styling** | QSS (`styles.qss`) | Dark-mode F1 paddock aesthetic with custom scrollbars and chat bubbles |
| **Local LLM** | Ollama (`llama3.1:8b`) | Private, zero-cost, offline race engineer persona |
| **Cloud Fallback** | OpenAI GPT-4o | Optional fallback if Ollama is not running locally |
| **Telemetry** | FastF1 / OpenF1 | Raw timing streams, lap records, and car sensor telemetry |
| **Visualisation** | Matplotlib (`Agg`) | Non-blocking background rendering of multi-tier telemetry graphs |
| **Weather API** | Open-Meteo | Live track surface and ambient temperature for 10 international circuits |

---

## Project Structure

```text
F1-Race-Engineer-AI-Powered-Desktop-Dashboard/
├── app/
│   ├── backend/
│   │   ├── engineer.py              # LLM worker loop, tool dispatch & circuit guardrails
│   │   ├── telemetry.py             # QThread Matplotlib chart generation & sensor loading
│   │   ├── weather.py               # Open-Meteo API client for 10 F1 circuits
│   │   └── perez_lap44_telemetry.csv # Cached raw sensor points (386 samples, Perez Lap 44)
│   ├── ui/
│   │   ├── chat_panel.py            # Chat interface, message bubbles & suggestion buttons
│   │   ├── dashboard.py             # Main window with horizontal QSplitter layout
│   │   ├── telemetry_panel.py       # Telemetry graph viewer with asynchronous refresh
│   │   └── styles.qss               # Modular dark-mode stylesheet
│   ├── knowledge_base.txt           # Verified technical engineering notes & setup heuristics
│   ├── main.py                      # Clean application entry point
│   └── telemetry_graph.png          # High-resolution fastest lap plot
├── f1_cache/
│   └── belgian_gp_2024_stints.json  # Cached 58-stint race distribution
├── .gitignore                       # Clean ignore rules for caches and sensitive keys
├── requirements.txt                 # Project dependencies
├── run.py                           # Main application launcher
└── stints.py                        # Standalone 58-stint strategy analysis pipeline
```

---

## Quick Start

### 1. Prerequisites
* Python 3.11+ (Python 3.13 recommended)
* [Ollama](https://ollama.com) installed and running

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/AbhidyuBehera26/F1-Race-Engineer-AI-Powered-Desktop-Dashboard.git
cd F1-Race-Engineer-AI-Powered-Desktop-Dashboard
pip install -r requirements.txt
```

### 3. Pull the Local LLM Model
Download the Llama 3.1 8B model (one-time download, ~4.7 GB):
```bash
ollama pull llama3.1:8b
```

### 4. Run the Dashboard
On Windows (using the Python launcher):
```bash
py run.py
```
*(Or on Linux/macOS: `python3 run.py`)*

### 5. Run the Stint Analysis Pipeline
To run the standalone strategy distribution analysis across all 58 Belgian GP stints:
```bash
python stints.py
```
*(Runs in under 0.1s using Python Standard Library with zero pip dependencies).*

---

## OpenAI Fallback (Optional)

If you prefer to run cloud-based GPT-4o instead of running Ollama locally:
1. Create a file named `openAI_key.txt` in the project root.
2. Paste your OpenAI API key inside.
3. Launch the dashboard without starting Ollama. The app detects the key and switches automatically.

*(Note: `openAI_key.txt` is listed in `.gitignore` and is never committed).*

---

## Example Debrief Queries

| User Prompt | System Behavior | Grounded Output |
| :--- | :--- | :--- |
| **"Tyres for Spa today?"** | Fetches live weather for Spa, reads 26.0/24.5 starting minimums, calculates cold-track adjustment in Python. | *Quotes Hard C2 / Medium C3 / Soft C4 with exact adjusted PSI.* |
| **"Tyres for Monza?"** | Code guardrail detects Monza has no tyre data in notes. | *"No tyre compound allocation or starting pressures are documented for Monza."* (Zero hallucination). |
| **"Best aero for Monza?"** | Retrieves low-drag circuit aerodynamic setup notes. | *Recommends 2° to 4° (or 2° to 6°) rear wing angle.* |
| **"Analyse the brake zones"** | Contextualizes the right-hand telemetry plot. | *Identifies Bus Stop chicane (100m board from 300+ km/h) and La Source (80m board).* |

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
