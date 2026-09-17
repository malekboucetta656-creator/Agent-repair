#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Any
import json
import os
import requests

class TaskReader:
    """Lit les commandes labes.pro via /api.php?action=orders_pending"""
    VERSION = "0.2.0-labes"
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
        tok = self.config.get("site",{}).get("token","")
        if str(tok).startswith("env:"):
            tok = os.environ.get(str(tok)[4:], "")
        h = {"Content-Type": "application/json"}
        if tok and tok != "changeme":
            h["Authorization"] = f"Bearer {tok}"
        return h

    def list_tasks(self) -> list[dict[str,Any]]:
        site = self.config.get("site",{})
        base = site.get("base_url","https://labes.pro")
        ep = site.get("endpoints",{}).get("list","/api.php?action=orders_pending")
        if "ton-site.com" in base:
            return self._mock_labs()
        # Si labes.pro sans token configuré -> tente sans auth (dev) puis mock
        try:
            url = base.rstrip("/") + ep
            r = requests.get(url, headers=self._headers(), timeout=15)
            if r.status_code == 401:
                # pas de token -> mock demo
                return self._mock_labs()
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list):
                return self._normalize_labs(data)
            if isinstance(data, dict):
                if "orders" in data:
                    return self._normalize_labs(data["orders"])
                if "error" in data:
                    # ex: orders_pending non implémenté côté PHP -> mock
                    print(f"[!] labes.pro API: {data} -> mock")
                    return self._mock_labs()
                return self._normalize_labs([data])
            return self._mock_labs()
        except Exception as e:
            print(f"[!] TaskReader labes.pro error: {e} -> mock")
            return self._mock_labs()

    def _normalize_labs(self, orders: list[dict]) -> list[dict]:
        out=[]
        for o in orders:
            # labes.pro order_create envoie: client_id, zone, adresse, type_velo, modele, panne, description
            out.append({
                "id": o.get("id") or o.get("order_id") or f"REP-{o.get('client_id','?')}",
                "type": o.get("type") or o.get("panne") or o.get("type_velo") or "autre",
                "description": o.get("description") or o.get("panne") or "",
                "adresse": o.get("adresse") or o.get("address") or "Paris",
                "lieu": o.get("zone") or "Paris",
                "client_tel": o.get("telephone") or o.get("client_tel") or o.get("whatsapp") or "",
                "client_nom": o.get("prenom") or o.get("client_nom") or "",
                "quantite": 1,
                "date_debut": o.get("creneau") or o.get("date") or "2026-09-18",
                "date_fin": o.get("creneau") or o.get("date") or "2026-09-18",
                "_raw": o
            })
        return out

    def _mock_labs(self):
        return [
            {"id": "LAB-101", "type": "crevaison", "description": "crevaison arrière - chambre à air", "adresse": "18 rue de Clignancourt, Paris 75018", "lieu": "Paris 18", "client_tel": "+33695806198", "client_nom": "Sophie M.", "quantite": 1, "date_debut": "2026-09-18", "date_fin": "2026-09-18"},
            {"id": "LAB-102", "type": "electrique", "description": "VAE Bosch ne répond plus - diagnostic", "adresse": "Rue de Rivoli, Paris 75004", "lieu": "Paris 04", "client_tel": "+33601000002", "client_nom": "Thomas R.", "quantite": 1, "date_debut": "2026-09-19", "date_fin": "2026-09-19"},
            {"id": "LAB-103", "type": "transmission", "description": "chaîne saute + dérailleur", "adresse": "Avenue des Gobelins, Paris 75013", "lieu": "Paris 13", "client_tel": "+33601000003", "client_nom": "Amina K.", "quantite": 1, "date_debut": "2026-09-20", "date_fin": "2026-09-20"},
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
