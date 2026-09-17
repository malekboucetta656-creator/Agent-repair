#!/usr/bin/env python3
from __future__ import annotations
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
from pathlib import Path

from agent.llm_analyzer import LLMAnalyzer
from agent.attributor import Attributor
from agent.whatsapp import WhatsApp
from agent.client_chat import handle_client_message, get_history

app = FastAPI(title="Agent Bike Webhook", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "agent": "Agent Bike", "version": "0.1.0"}

@app.post("/webhook/repair")
async def webhook_repair(request: Request):
    try:
        task = await request.json()
    except:
        return JSONResponse({"error": "invalid json"}, status_code=400)
    # validation déterministe
    if not task.get("id"):
        return JSONResponse({"error": "missing id"}, status_code=422)

    an = LLMAnalyzer()
    at = Attributor()
    wa = WhatsApp()

    analysis = an.analyze(task)
    assign = at.assign(task, analysis, dry_run=False if Path("config/config.yaml").exists() else True)
    notif = wa.notify_assignment(task, assign, dry_run=assign.get("dry_run", True))

    # log
    Path("logs").mkdir(exist_ok=True)
    log = {"task": task, "analysis": analysis, "assign": assign, "notif": notif}
    Path("logs/webhook_last.json").write_text(json.dumps(log, indent=2, ensure_ascii=False))

    return {"status": "DISPATCHED" if assign.get("validated") else "REJECTED", **log}

@app.get("/tasks")
def list_tasks():
    p = Path("logs/last_run.json")
    if p.exists():
        return json.loads(p.read_text())
    return []

@app.post("/webhook/whatsapp")
async def whatsapp_inbound(request: Request):
    """Client répond sur WhatsApp → Agent Bike comprend + suivi"""
    try:
        data = await request.json()
    except:
        # Twilio envoie form-encoded
        form = await request.form()
        data = dict(form)
    # normalise: From, Body, task_id
    from_tel = data.get("From") or data.get("from") or data.get("client_tel") or "unknown"
    body = data.get("Body") or data.get("body") or data.get("message") or data.get("text") or ""
    task_id = data.get("task_id") or data.get("id") or "LAB-101"
    # enlève whatsapp: prefix
    if from_tel.startswith("whatsapp:"):
        from_tel = from_tel[len("whatsapp:"):]
    result = handle_client_message(task_id, body, task=None)
    # auto-réponse WhatsApp (dry_run si pas de token)
    wa = WhatsApp()
    wa.send(from_tel, result["reply"], dry_run=True)  # passer False en prod
    return {"status": "replied", **result}

@app.get("/chat/{task_id}")
def chat_history(task_id: str):
    return {"task_id": task_id, "history": get_history(task_id)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
