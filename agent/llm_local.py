#!/usr/bin/env python3
from __future__ import annotations
import requests, json, os
from pathlib import Path

# Local LLM via Ollama (sans cloud, sans clé)
# Install: curl -fsSL https://ollama.com/install.sh | sh && ollama pull mistral
# Alternative: llama.cpp, LM Studio (même API)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "mistral")  # ou llama3.1, gemma2

def is_available() -> bool:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return r.status_code == 200
    except:
        return False

def call_local(prompt: str, system: str = "", model: str | None = None) -> str | None:
    if not is_available():
        return None
    m = model or DEFAULT_MODEL
    try:
        # Chat mode si system fourni
        payload = {
            "model": m,
            "prompt": (f"{system}\n\n{prompt}" if system else prompt),
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 300}
        }
        r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data.get("response", "").strip()
    except Exception as e:
        return None

def analyze_local(task: dict, client_msg: str = "", history: list | None = None) -> dict | None:
    """Analyse panne via LLM local — même JSON que llm_chat"""
    system = "Tu es Agent Bike labes.pro. Réponds JSON strict: {\"category\":\"crevaison|frein|transmission|electrique|autre\",\"difficulte\":\"facile|moyen|difficile\",\"duree_min\":30,\"pieces\":[],\"distance_km\":5,\"proche\":true}"
    prompt = f"Tâche: {json.dumps(task, ensure_ascii=False)}\nClient: {client_msg}\nHist: {history or []}\nJSON seul:"
    txt = call_local(prompt, system=system)
    if not txt:
        return None
    import re
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return {"_error": "no json", "raw": txt}
    try:
        j = json.loads(m.group(0))
        j["llm"] = f"local:{DEFAULT_MODEL}"
        return j
    except:
        return {"_error": "parse", "raw": txt}

if __name__ == "__main__":
    print("ollama dispo:", is_available())
    if is_available():
        print(call_local("Bonjour, c'est quoi une crevaison ?", system="Tu es mécano vélo"))
    else:
        print("Ollama non lancé — fallback heuristique actif")
