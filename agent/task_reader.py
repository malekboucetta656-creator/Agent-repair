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
            {"id": "LOC-101", "type": "velo_electrique", "quantite": 2, "date_debut": "2026-09-18", "date_fin": "2026-09-20", "lieu": "Alger - Bab Ezzouar", "client_tel": "+213550000001", "client_nom": "Amine", "description": "2 vélos électriques pour week-end"},
            {"id": "LOC-102", "type": "vtt", "quantite": 1, "date_debut": "2026-09-19", "date_fin": "2026-09-19", "lieu": "Oran", "client_tel": "+213550000002", "client_nom": "Sara", "description": "VTT pour journée"},
            {"id": "LOC-103", "type": "velo_classique", "quantite": 4, "date_debut": "2026-09-20", "date_fin": "2026-09-22", "lieu": "Constantine", "client_tel": "+213550000003", "client_nom": "Yacine", "description": "4 vélos classiques famille"},
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
