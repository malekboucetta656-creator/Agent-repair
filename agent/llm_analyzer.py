#!/usr/bin/env python3
from __future__ import annotations
from typing import Any

class LLMAnalyzer:
    VERSION="0.1.0"
    def analyze(self, task: dict[str,Any]) -> dict[str,Any]:
        # Délègue à LLMChat (ChatGPT/Claude) si dispo, sinon heuristique
        try:
            from agent.llm_chat import LLMChat
            return LLMChat().analyze(task)
        except Exception:
            pass
        t = (task.get("type","") + " " + task.get("description","")).lower()
        quantite = task.get("quantite", 1)
        if "electrique" in t or "ebike" in t:
            cat="electrique"; skill="electrique"; est="diagnostic 90min"
        elif "vtt" in t:
            cat="vtt"; skill="vtt"; est="VTT 60min"
        elif "crevaison" in t or "pneu" in t:
            cat="crevaison"; skill="facile"; est="30min"
        elif "frein" in t:
            cat="frein"; skill="frein"; est="45min"
        elif "chaine" in t or "transmission" in t:
            cat="transmission"; skill="transmission"; est="60min"
        else:
            cat=task.get("type","autre"); skill=cat; est="45min"
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
            "confidence": 90 if cat in ["crevaison","frein","transmission"] else 65,
            "llm": "heuristic"
        }
