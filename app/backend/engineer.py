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
SYSTEM_PROMPT = """You are a Chief Race Engineer for a professional motorsport team. You are blunt, precise,
and entirely focused on lap time. You don't give vague advice — you give numbers.

Rules:
1. Before recommending any tyre compound or pressure, ALWAYS call get_track_weather first.
2. For setup questions (aero, brakes, suspension), ALWAYS call search_knowledge_base and quote the figures.
3. Be specific: PSI values, wing angles in degrees, brake points in metres.
4. Keep responses concise and use bullet points for numerical data."""

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


def search_knowledge_base(query: str) -> str:
    # Read the local knowledge base file and return the best matching sections
    try:
        content = KB_PATH.read_text(encoding='utf-8')
    except FileNotFoundError:
        return "Knowledge base file not found."

    # Split contents by section headers (##)
    sections = re.split(r'\n(?=## )', content)
    query_words = set(re.sub(r'[^\w\s]', '', query.lower()).split())

    # Score each section based on matching keywords
    scored = []
    for s in sections:
        score = 0
        for w in query_words:
            if len(w) > 2 and w in s.lower():
                score += 1
        scored.append((score, s.strip()))
    
    # Sort from highest to lowest score
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # Select the top 2 matching sections
    top_matches = []
    for score, s in scored:
        if score > 0:
            top_matches.append(s)
            if len(top_matches) == 2:
                break
                
    if top_matches:
        return '\n\n---\n\n'.join(top_matches)
    return "No specific data found. Rely on general engineering principles."


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
                '🦙 Ollama (Llama 3.1 8B — Local)'
            )
    except Exception:
        pass

    # Try OpenAI fallback
    api_key = _read_openai_key()
    if api_key:
        print("Using OpenAI GPT-4o...")
        return OpenAI(api_key=api_key), 'gpt-4o', '☁️ OpenAI (GPT-4o)'

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
        status_cb(f"🔧 Running tool {name}({params_str})")

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
            status_callback(f"🤔 Thinking... (round {round_num + 1})")

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
                
                print(f"Executing: {tool_name} with {tool_args}")
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
