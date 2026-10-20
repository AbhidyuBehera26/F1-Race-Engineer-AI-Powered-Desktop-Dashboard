import json
import os
import re
import requests
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from app.backend.weather import get_track_weather

# File path for the knowledge base
KB_PATH = Path(__file__).parent.parent / 'knowledge_base.txt'

# System prompt for the race engineer persona
SYSTEM_PROMPT = """You are an F1 Race Engineering Assistant specializing in vehicle dynamics, strategy, and tyre management. You provide precise, quantified technical recommendations grounded strictly in verified setup notes and live track conditions.

Rules:
1. For tyre, pressure, or setup questions, call search_knowledge_base(query) to retrieve circuit-specific notes.
2. Quote ONLY the specific tyre compounds and starting pressures listed in the notes. If the notes state that tyre allocations or pressures are not documented for a circuit, repeat that exact notice without inventing figures.
3. For aero, brake balance, suspension, and strategy questions, quote the exact values from the notes.
4. Keep responses concise and format numerical data clearly with bullet points."""

# Definitions of tools for the LLM to call
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_track_weather",
            "description": (
                "Gets current live weather at a motorsport circuit: air temp, track surface temp, "
                "rain, wind speed, humidity. Call this before ANY tyre or setup recommendation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "track_name": {
                        "type": "string",
                        "description": "Circuit name, e.g. 'spa', 'monza', 'silverstone'."
                    }
                },
                "required": ["track_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Searches the F1 engineering knowledge base for tyre compounds, pressures, "
                "aerodynamic settings, brake balance, suspension, and circuit notes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query, e.g. 'tyre pressure soft compound' or 'Spa aero setup'."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

CIRCUITS = [
    'spa', 'monza', 'silverstone', 'bahrain', 'monaco',
    'suzuka', 'interlagos', 'barcelona', 'nurburgring'
]

def _extract_target_circuit(query_lower: str) -> str | None:
    for circuit in CIRCUITS:
        if circuit in query_lower:
            return circuit
    return None

def _is_tyre_query(query_lower: str) -> bool:
    keywords = ['tyre', 'tyres', 'tire', 'tires', 'typr', 'compound', 'pressure', 'psi', 'rubber']
    for kw in keywords:
        if kw in query_lower:
            return True
    return False

def _find_circuit_section(target_circuit: str, sections: list) -> str | None:
    target = target_circuit.lower()
    for s in sections:
        stripped = s.strip()
        header = stripped.split('\n')[0].lower()
        if header.startswith(f'## {target}') or header.startswith(f'## {target}-'):
            return stripped
    return None

def _has_tyre_data(section: str) -> bool:
    low = section.lower()
    return ('recommended tyre' in low) or ('starting pressures' in low)

def _build_spa_tyre_response() -> str:
    # 1. Fetch live weather directly in Python so 8B model doesn't need to chain tools
    track_temp = None
    weather_desc = "Live weather data unavailable"
    try:
        w_data = json.loads(get_track_weather('spa'))
        if 'track_surface_temp_c' in w_data:
            track_temp = w_data['track_surface_temp_c']
            air_temp = w_data.get('air_temp_c', 'N/A')
            cond = w_data.get('conditions', 'DRY')
            weather_desc = f"Air {air_temp} deg C, Track surface {track_temp} deg C, Conditions: {cond}"
    except Exception:
        pass

    # 2. Baseline Pirelli starting pressures
    base_front = 26.0
    base_rear = 24.5

    # 3. Deterministic Python temperature correction
    if track_temp is not None and track_temp < 30.0:
        f_low = base_front + 1.5
        f_high = base_front + 2.0
        r_low = base_rear + 1.5
        r_high = base_rear + 2.0
        adj_text = (
            f"\n- Track surface is cold ({track_temp} deg C < 30 deg C). Cold-track correction (+1.5 to +2.0 PSI rule of thumb applied):\n"
            f"  - Recommended Adjusted Pressures: Front {f_low:.1f} to {f_high:.1f} PSI, Rear {r_low:.1f} to {r_high:.1f} PSI"
        )
    else:
        adj_text = f"\n- Track surface temperature ({track_temp} deg C) is warm (>= 30 deg C). Baseline minimums apply."

    return (
        "## Spa-Francorchamps Tyre Specification & Starting Pressures\n"
        "- Nominated Compounds: Hard C2, Medium C3, Soft C4 (Pirelli 2024 nomination)\n"
        f"- Mandatory Baseline Minimum Starting Pressures: Front {base_front:.1f} PSI, Rear {base_rear:.1f} PSI\n"
        f"- Live Weather: {weather_desc}"
        f"{adj_text}\n"
        "- Camber limits: Front -2.75 deg, Rear -1.50 deg\n"
        "- Note: All four wheels take the same compound; do not assign different compounds to front and rear axles."
    )

def search_knowledge_base(query: str) -> str:
    # Read the local knowledge base file and return the best matching sections
    try:
        content = KB_PATH.read_text(encoding='utf-8')
    except FileNotFoundError:
        return "Knowledge base file not found."

    query_lower = query.lower()
    sections = re.split(r'\n(?=## )', content)

    target_circuit = _extract_target_circuit(query_lower)

    # Circuit-specific guard: if a known circuit is in the query, strictly isolate to that circuit
    if target_circuit:
        circuit_section = _find_circuit_section(target_circuit, sections)
        
        # If circuit has no section documented at all
        if circuit_section is None:
            return f"No notes documented for {target_circuit.capitalize()}."

        # If it's Spa and asking about tyres
        if target_circuit == 'spa' and _is_tyre_query(query_lower):
            return _build_spa_tyre_response()

        # If the circuit section lacks tyre data (e.g. Monza, Silverstone)
        if not _has_tyre_data(circuit_section):
            guard_note = (
                f"\n\nNOTE: No tyre compound allocation or starting pressures are documented for "
                f"{target_circuit.capitalize()}. Do not invent or guess figures."
            )
            # If the user specifically asks about tyres, return only the guard note
            if _is_tyre_query(query_lower):
                return guard_note.strip()
            # If asking about aero/setup, return the section with the guard note attached
            return circuit_section + guard_note

        return circuit_section

    # Default keyword search for general setup, aero, or race strategy queries
    query_words = set(re.sub(r'[^\w\s]', '', query_lower).split())
    scored = []
    for s in sections:
        score = 0
        for w in query_words:
            if len(w) > 2 and w in s.lower():
                score += 1
        scored.append((score, s.strip()))

    scored.sort(key=lambda x: x[0], reverse=True)

    top_matches = []
    for score, s in scored:
        if score > 0:
            top_matches.append(s)
            if len(top_matches) == 2:
                break

    if top_matches:
        return '\n\n---\n\n'.join(top_matches)
    return "No matching notes found."


def _read_openai_key() -> str | None:
    # Get the OpenAI key from the text file or environment variables
    key_file = Path(__file__).parent.parent.parent / 'openAI_key.txt'
    try:
        key = key_file.read_text().strip()
        if key and not key.startswith('#'):
            return key
    except FileNotFoundError:
        pass
    return os.environ.get('OPENAI_API_KEY')


def _detect_backend() -> tuple:
    # Use local Ollama (Llama 3.1) if it is running, otherwise use OpenAI
    from openai import OpenAI

    # Try local Ollama
    try:
        r = requests.get('http://localhost:11434/api/tags', timeout=2)
        if r.status_code == 200:
            print("Found local Ollama server. Using Llama 3.1...")
            return (
                OpenAI(base_url='http://localhost:11434/v1', api_key='ollama'),
                'llama3.1:8b',
                'Ollama (Llama 3.1 8B - Local)'
            )
    except Exception:
        pass

    # Try OpenAI fallback
    api_key = _read_openai_key()
    if api_key:
        print("Using OpenAI GPT-4o...")
        return OpenAI(api_key=api_key), 'gpt-4o', 'OpenAI (GPT-4o)'

    raise RuntimeError(
        "No LLM available. Start Ollama locally or put your OpenAI key in openAI_key.txt."
    )


def _dispatch_tool(name: str, arguments_str: str, status_cb=None) -> str:
    # Parse arguments from the model and call the correct tool function
    try:
        args = json.loads(arguments_str)
    except Exception as e:
        return json.dumps({"error": f"Failed to parse arguments: {str(e)}"})

    if status_cb:
        params_list = []
        for k, v in args.items():
            params_list.append(f"{k}={v!r}")
        params_str = ', '.join(params_list)
        status_cb(f"Running tool {name}({params_str})")

    # Run tool based on name
    if name == 'get_track_weather':
        return get_track_weather(args.get('track_name', ''))
    elif name == 'search_knowledge_base':
        return search_knowledge_base(args.get('query', ''))
        
    return json.dumps({"error": f"Unknown tool: {name}"})


def get_ai_response(message: str, history: list, status_callback=None) -> tuple[str, str]:
    # Query backend LLM and process tool calls in a loop (up to 8 times max)
    client, model, backend_label = _detect_backend()

    # Format the message history
    messages = []
    messages.append({"role": "system", "content": SYSTEM_PROMPT})
    for h in history:
        messages.append(h)
    messages.append({"role": "user", "content": message})

    for round_num in range(8):
        print(f"Turn {round_num + 1} starting...")
        if status_callback:
            status_callback(f"Thinking... (round {round_num + 1})")

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.4,
        )
        choice = response.choices[0]

        # Check if the LLM wants to run functions
        if choice.finish_reason == 'tool_calls' and choice.message.tool_calls:
            print(f"LLM requested tool calls: {choice.message.tool_calls}")
            
            tool_calls_list = []
            for tc in choice.message.tool_calls:
                tool_calls_list.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })
            
            messages.append({
                "role": "assistant",
                "content": choice.message.content,
                "tool_calls": tool_calls_list
            })
            
            # Execute tools one by one
            for tc in choice.message.tool_calls:
                tool_name = tc.function.name
                tool_args = tc.function.arguments
                
                print("tool:", tool_name, tool_args)
                tool_result = _dispatch_tool(tool_name, tool_args, status_callback)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_result
                })
        else:
            print("Finished query loop.")
            return choice.message.content or "No response generated.", backend_label

    return "Maximum tool call rounds reached.", backend_label


class LLMWorkerThread(QThread):
    # PyQt thread for executing the LLM loop in the background so GUI doesn't freeze
    finished = pyqtSignal(str, str)
    status_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, message: str, history: list):
        super().__init__()
        self.message = message
        self.history = history

    def run(self):
        try:
            response, backend = get_ai_response(
                self.message, 
                self.history,
                status_callback=self.status_updated.emit
            )
            self.finished.emit(response, backend)
        except Exception as e:
            self.error_occurred.emit(str(e))
