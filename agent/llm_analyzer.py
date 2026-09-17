#!/usr/bin/env python3
from __future__ import annotations
from typing import Any

class LLMAnalyzer:
    VERSION="0.1.0"
    def analyze(self, task: dict[str,Any]) -> dict[str,Any]:
        t = (task.get("type","") + " " + task.get("description","")).lower()
        quantite = task.get("quantite", 1)
        # Vélo location
        if "electrique" in t or "ebike" in t or "vae" in t:
            cat="velo_electrique"; skill="ebike"; est="batterie OK, casque inclus"
        elif "vtt" in t:
            cat="vtt"; skill="vtt"; est="VTT + casque"
        elif "enfant" in t:
            cat="velo_enfant"; skill="enfant"; est="vélo enfant + roulette"
        elif "classique" in t or "velo" in t:
            cat="velo_classique"; skill="classique"; est="vélo classique"
        else:
            cat=task.get("type","velo_classique"); skill="classique"; est="à confirmer"
        # urgence basée sur date_debut
        urgence = "haute" if "2026-09-18" in str(task.get("date_debut")) else "moyenne"
        if quantite >= 4:
            urgence = "haute"
        return {
            "task_id": task.get("id"),
            "category": cat,
            "urgence": urgence,
            "skill_needed": skill,
            "quantite": quantite,
            "estimation": est,
            "reason": f"type='{task.get('type')}' x{quantite} → {cat}/{urgence}",
            "validator": "stock_match",
            "confidence": 90 if cat in ["velo_electrique","vtt","velo_classique"] else 65
        }
