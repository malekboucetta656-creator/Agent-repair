#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Any
import json, os
import requests

MEMORY = Path("logs/conversations.json")
MEMORY.parent.mkdir(exist_ok=True)

SYSTEM = """Tu es Agent Bike (labes.pro) — mécano cargo Aubervilliers → Paris.
Tu réponds aux clients sur WhatsApp pour comprendre leur besoin et faire le suivi.
- Ton: pro, chaleureux, court, en français
- Objectif: clarifier panne, adresse Paris, créneau, photo si besoin
- Ne jamais inventer prix: rappelle 15€ facile / 30€ moyen / 50€ VAE (labes.pro) + pièces en sus devis sur place
- Si infos manquent, pose 1 question à la fois
- Si client confirme, dis: 'Parfait, mécano cargo arrive en <24h'
Réponds JSON: {"reply": "texte WhatsApp", "need": ["adresse"|"photo"|"creneau"], "update": {"type": "..."}}
"""

def _load_memory() -> dict:
    if MEMORY.exists():
        try: return json.loads(MEMORY.read_text())
        except: return {}
    return {}

def _save_memory(m: dict):
    MEMORY.write_text(json.dumps(m, indent=2, ensure_ascii=False))

def _call_llm(task: dict, client_msg: str, history: list) -> dict:
    # Try ChatGPT
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key)
            ctx = f"Tâche: {json.dumps(task, ensure_ascii=False)}\nHistorique: {history}\nClient: {client_msg}"
            r = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"system","content":SYSTEM},{"role":"user","content":ctx}], temperature=0.4, response_format={"type":"json_object"})
            return json.loads(r.choices[0].message.content)
        except Exception as e:
            pass
    # Try Claude
    key2 = os.environ.get("ANTHROPIC_API_KEY")
    if key2:
        try:
            import anthropic
            c = anthropic.Anthropic(api_key=key2)
            m = c.messages.create(model="claude-3-5-sonnet-20241022", max_tokens=400, system=SYSTEM, messages=[{"role":"user","content": f"Tâche {json.dumps(task)} hist {history} client: {client_msg} JSON seul"}])
            import re
            txt=m.content[0].text
            j=re.search(r"\{.*\}", txt, re.S)
            return json.loads(j.group(0)) if j else {"reply": txt}
        except: pass
    # Heuristique fallback
    msg = client_msg.lower()
    need=[]
    if "adresse" not in str(task.get("adresse")).lower() or len(task.get("adresse",""))<10:
        need.append("adresse")
    if "photo" in msg or "image" in msg:
        need=[]
        reply="Merci pour la photo ! J'ai bien reçu. Le mécano prépare le matériel cargo. 📸"
    elif "crevaison" in msg or "pneu" in msg:
        reply="Compris, crevaison. C'est 15€ MO (chambre à air en sus ~8€). Vous êtes à quelle adresse exacte à Paris ? Et créneau souhaité (matin/aprem) ?"
        need=["adresse","creneau"]
    elif "frein" in msg:
        reply="Noté, frein. 30€ MO max (patins/câble en sus). Photo du frein possible ? Et adresse Paris ?"
        need=["photo","adresse"]
    elif "adresse" in msg or "paris" in msg:
        reply="Parfait, adresse notée. Mécano cargo Aubervilliers → Paris en vélo, il passe en <24h. Créneau préféré ?"
        need=["creneau"]
    elif "creneau" in msg or "demain" in msg or "matin" in msg:
        reply="Créneau noté. Vous recevrez confirmation WhatsApp + suivi. Paiement uniquement le jour du RDV. À demain ! ✅"
        need=[]
    else:
        reply="Merci pour votre message ! Pour mieux comprendre : c'est quelle panne (crevaison/freins/VAE) et à quelle adresse à Paris ?"
        need=["adresse"]
    return {"reply": reply, "need": need, "update": {}}

def handle_client_message(task_id: str, client_msg: str, task: dict | None = None) -> dict[str, Any]:
    mem = _load_memory()
    hist = mem.get(task_id, [])
    hist.append({"from": "client", "msg": client_msg})
    # task fallback
    if not task:
        from agent.task_reader import TaskReader
        task = TaskReader().get(task_id) or {"id": task_id, "adresse": "Paris", "type": "autre"}
    result = _call_llm(task, client_msg, hist)
    reply = result.get("reply","Merci, on revient vers vous !")
    hist.append({"from": "agent", "msg": reply})
    mem[task_id] = hist[-20:]  # garde 20 derniers
    _save_memory(mem)
    # update task si besoin
    update = result.get("update",{})
    need = result.get("need",[])
    # log suivi
    Path("logs").mkdir(exist_ok=True)
    Path(f"logs/chat_{task_id}.json").write_text(json.dumps({"task": task, "history": hist, "need": need, "update": update}, indent=2, ensure_ascii=False))
    return {"task_id": task_id, "reply": reply, "need": need, "update": update, "history": hist, "whatsapp_ready": reply}

def get_history(task_id: str) -> list:
    return _load_memory().get(task_id, [])

if __name__=="__main__":
    import json
    print(json.dumps(handle_client_message("LAB-101", "Bonjour, j'ai une crevaison à Paris 18"), indent=2, ensure_ascii=False))
