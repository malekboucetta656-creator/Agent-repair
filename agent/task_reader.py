#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Any
import json
import os
import requests

class TaskReader:
    """Lit les demandes de location vélo depuis ton site (API)"""
    VERSION = "0.1.0"
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config/config.yaml"
        self.config = self._load(config_path)

    def _load(self, p):
        path = Path(p)
        if not path.exists():
            path = Path(__file__).parent.parent / "config/config.example.yaml"
        if path.exists():
            import yaml
            return yaml.safe_load(path.read_text()) or {}
        return {}

    def _headers(self):
        site = self.config.get("site",{})
        tok = site.get("token","")
        if str(tok).startswith("env:"):
            tok = os.environ.get(str(tok)[4:], "")
        return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"} if tok else {}

    def list_tasks(self) -> list[dict[str,Any]]:
        site = self.config.get("site",{})
        base = site.get("base_url","")
        ep = site.get("endpoints",{}).get("list","/rentals?status=pending")
        if not base or "ton-site.com" in base:
            return self._mock_tasks()
        try:
            url = base.rstrip("/") + ep
            r = requests.get(url, headers=self._headers(), timeout=15)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "tasks" in data:
                return data["tasks"]
            if isinstance(data, dict) and "rentals" in data:
                return data["rentals"]
            return [data]
        except Exception as e:
            return [{"_error": str(e), "_mock_fallback": self._mock_tasks()[0]}]

    def _mock_tasks(self):
        return [
            {"id": "REP-101", "type": "crevaison", "quantite": 1, "date_debut": "2026-09-18", "date_fin": "2026-09-18", "lieu": "Paris", "adresse": "18 rue de Clignancourt, Paris 75018", "client_tel": "+33601000001", "client_nom": "Amine", "description": "crevaison arrière - facile"},
            {"id": "REP-102", "type": "frein", "quantite": 1, "date_debut": "2026-09-19", "date_fin": "2026-09-19", "lieu": "Paris", "adresse": "Rue de Rivoli, Paris 75004", "client_tel": "+33601000002", "client_nom": "Sara", "description": "frein avant qui frotte"},
            {"id": "REP-103", "type": "transmission", "quantite": 1, "date_debut": "2026-09-20", "date_fin": "2026-09-20", "lieu": "Paris", "adresse": "Avenue des Gobelins, Paris 75013", "client_tel": "+33601000003", "client_nom": "Yacine", "description": "chaine saute - transmission"},
        ]

    def get(self, task_id: str) -> dict:
        for t in self.list_tasks():
            if t.get("id")==task_id:
                return t
        return {}

if __name__ == "__main__":
    import sys
    tr = TaskReader(sys.argv[1] if len(sys.argv)>1 else None)
    print(json.dumps(tr.list_tasks(), indent=2, ensure_ascii=False))
