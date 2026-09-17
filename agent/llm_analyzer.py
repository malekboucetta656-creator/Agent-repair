#!/usr/bin/env python3
from __future__ import annotations
from typing import Any

class LLMAnalyzer:
    VERSION="0.1.0"
    def analyze(self, task: dict[str,Any]) -> dict[str,Any]:
        desc = (task.get("description","") + " " + task.get("type","")).lower()
        # Heuristique + LLM placeholder
        if "fuite" in desc or "eau" in desc or "plomberie" in desc:
            cat="plomberie"; prio="haute"; skill="plombier"; est="1-2h"
        elif "clim" in desc or "hvac" in desc:
            cat="climatisation"; prio="moyenne"; skill="hvac"; est="2-4h"
        elif "elec" in desc:
            cat="electricite"; prio="haute"; skill="electricien"; est="1-3h"
        else:
            cat=task.get("type","misc"); prio=task.get("urgence","moyenne"); skill="general"; est="à estimer"
        return {
            "task_id": task.get("id"),
            "category": cat,
            "urgence": prio,
            "skill_needed": skill,
            "estimation": est,
            "reason": f"desc='{task.get('description')}' → {cat}/{prio}",
            "validator": "site_skill_match",
            "confidence": 85 if cat!="misc" else 60
        }
