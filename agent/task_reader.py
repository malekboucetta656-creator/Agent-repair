#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Any
import json
import os
import requests
import yaml

class TaskReader:
    """Lit les demandes depuis ton site (API) — déterministe"""
    VERSION = "0.1.0"
    def __init__(self, config_path="config/config.yaml"):
        self.config = self._load(config_path)

    def _load(self, p):
        path = Path(p)
        if not path.exists():
            path = Path("config/config.example.yaml")
        if path.exists():
            import yaml
            return yaml.safe_load(path.read_text()) or {}
        return {}

    def _headers(self):
        site = self.config.get("site",{})
        tok = site.get("token","")
        if tok.startswith("env:"):
            tok = os.environ.get(tok[4:], "")
        return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"} if tok else {}

    def list_tasks(self) -> list[dict[str,Any]]:
        site = self.config.get("site",{})
        base = site.get("base_url","")
        ep = site.get("endpoints",{}).get("list","/repairs?status=pending")
        # Si pas de site configuré -> mock pour demo
        if not base or "ton-site.com" in base:
            return self._mock_tasks()
        try:
            url = base.rstrip("/") + ep
            r = requests.get(url, headers=self._headers(), timeout=15)
            r.raise_for_status()
            data = r.json()
            # normalise: attend list ou {tasks: []}
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "tasks" in data:
                return data["tasks"]
            return [data]
        except Exception as e:
            return [{"_error": str(e), "_mock_fallback": self._mock_tasks()[0]}]

    def _mock_tasks(self):
        return [
            {"id": "REP-101", "type": "plomberie", "adresse": "Alger Centre", "client_tel": "+213550000001", "description": "Fuite eau cuisine", "urgence": "haute"},
            {"id": "REP-102", "type": "climatisation", "adresse": "Oran", "client_tel": "+213550000002", "description": "Clim HS", "urgence": "moyenne"},
        ]

    def get(self, task_id: str) -> dict:
        for t in self.list_tasks():
            if t.get("id")==task_id:
                return t
        return {}

if __name__ == "__main__":
    import sys
    tr = TaskReader(sys.argv[1] if len(sys.argv)>1 else "config/config.yaml")
    print(json.dumps(tr.list_tasks(), indent=2, ensure_ascii=False))
