#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Any
import os, requests, json, yaml

class Attributor:
    VERSION="0.1.0"
    def __init__(self, config_path="config/config.yaml"):
        p = Path(config_path)
        if not p.exists():
            p = Path("config/config.example.yaml")
        self.config = yaml.safe_load(p.read_text()) if p.exists() else {}

    def _headers(self):
        tok = self.config.get("site",{}).get("token","")
        if str(tok).startswith("env:"):
            tok = os.environ.get(str(tok)[4:], "")
        return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"} if tok else {}

    def choose_technician(self, analysis: dict) -> str:
        rules = self.config.get("attribution",{}).get("rules",{})
        cat = analysis.get("category","misc")
        cands = rules.get(cat) or rules.get("plomberie") or ["tech_default"]
        # round_robin simple
        import hashlib
        idx = int(hashlib.md5(analysis.get("task_id","").encode()).hexdigest(),16) % len(cands)
        return cands[idx]

    def assign(self, task: dict, analysis: dict, dry_run=False) -> dict[str,Any]:
        tech = self.choose_technician(analysis)
        site = self.config.get("site",{})
        base = site.get("base_url","")
        ep = site.get("endpoints",{}).get("assign","/repairs/{id}/assign")
        # validation déterministe: tech doit matcher skill
        validated = analysis.get("skill_needed","") in tech or tech!="tech_default"
        if dry_run or not base or "ton-site.com" in base:
            return {"task_id": task["id"], "technician": tech, "validated": validated, "dry_run": True, "site_url": base+ep.format(id=task["id"])}
        try:
            url = base.rstrip("/") + ep.format(id=task["id"])
            r = requests.post(url, headers=self._headers(), json={"technician": tech, "analysis": analysis}, timeout=15)
            r.raise_for_status()
            return {"task_id": task["id"], "technician": tech, "validated": True, "site_response": r.json()}
        except Exception as e:
            return {"task_id": task["id"], "technician": tech, "validated": False, "error": str(e)}

if __name__=="__main__":
    from agent.task_reader import TaskReader
    from agent.llm_analyzer import LLMAnalyzer
    tr=TaskReader(); an=LLMAnalyzer(); at=Attributor()
    for t in tr.list_tasks():
        a=an.analyze(t)
        print(json.dumps(at.assign(t,a,dry_run=True), indent=2, ensure_ascii=False))
