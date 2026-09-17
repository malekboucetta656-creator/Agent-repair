#!/usr/bin/env python3
from __future__ import annotations
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
from pathlib import Path

from agent.llm_analyzer import LLMAnalyzer
from agent.attributor import Attributor
from agent.whatsapp import WhatsApp

app = FastAPI(title="RepairFlow Webhook", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "agent": "RepairFlow", "version": "0.1.0"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
