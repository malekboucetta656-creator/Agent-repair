#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Any
import os

# Config: Bureau Aubervilliers (base cargo vélo)
BUREAU = {"name": "Bureau Aubervilliers", "lat": 48.9147, "lon": 2.3844, "adresse": "Aubervilliers (93)"}

PROMPT_SYSTEM = """Tu es RepairFlow pour réparations vélo à domicile en cargo vélo.
Base: Aubervilliers (48.9147, 2.3844). Interventions uniquement Paris.
Analyse chaque demande et réponds JSON strict:
{"category": "crevaison|frein|transmission|electrique|autre", "difficulte": "facile|moyen|difficile", "duree_min": 30, "pieces": [], "distance_km": 5.2, "proche": true}
"""

class LLMChat:
    VERSION="0.2.0"
    def __init__(self, config_path=None):
        p = Path(config_path) if config_path else Path(__file__).parent.parent / "config/config.yaml"
        if not p.exists():
            p = Path(__file__).parent.parent / "config/config.example.yaml"
        import yaml
        self.config = yaml.safe_load(p.read_text()) if p.exists() else {}

    def _call_openai(self, task: dict) -> dict | None:
        key = os.environ.get("OPENAI_API_KEY") or self.config.get("llm",{}).get("openai_key")
        if str(key).startswith("env:"): key = os.environ.get(str(key)[4:])
        if not key or "changeme" in str(key):
            return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key)
            content = f"Tâche: {task}"
            resp = client.chat.completions.create(
                model=self.config.get("llm",{}).get("model","gpt-4o-mini"),
                messages=[{"role":"system","content":PROMPT_SYSTEM},{"role":"user","content": content}],
                temperature=0.2, response_format={"type":"json_object"}
            )
            import json
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            return {"_error": f"openai:{e}"}

    def _call_claude(self, task: dict) -> dict | None:
        key = os.environ.get("ANTHROPIC_API_KEY") or self.config.get("llm",{}).get("claude_key")
        if str(key).startswith("env:"): key = os.environ.get(str(key)[4:])
        if not key or "changeme" in str(key):
            return None
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            import json
            msg = client.messages.create(
                model=self.config.get("llm",{}).get("claude_model","claude-3-5-sonnet-20241022"),
                max_tokens=500,
                system=PROMPT_SYSTEM,
                messages=[{"role":"user","content": f"Tâche: {json.dumps(task, ensure_ascii=False)} Réponds JSON seul."}]
            )
            txt = msg.content[0].text
            # extrait JSON
            import re
            m=re.search(r"\{.*\}", txt, re.S)
            return json.loads(m.group(0)) if m else {"raw": txt}
        except Exception as e:
            return {"_error": f"claude:{e}"}

    def analyze(self, task: dict) -> dict[str, Any]:
        # 1. Try ChatGPT
        r = self._call_openai(task)
        if r and "_error" not in r:
            r["llm"]="chatgpt"; r["task_id"]=task.get("id")
            # normalise
            r.setdefault("urgence", "moyenne"); r.setdefault("confidence", 85); r.setdefault("reason", f"ChatGPT {r.get('category')}")
            r.setdefault("quantite", task.get("quantite",1)); r.setdefault("skill_needed", r.get("category","autre"))
            return r
        # 2. Try Claude
        r2 = self._call_claude(task)
        if r2 and "_error" not in r2:
            r2["llm"]="claude"; r2["task_id"]=task.get("id")
            r2.setdefault("urgence", "moyenne"); r2.setdefault("confidence", 85); r2.setdefault("reason", f"Claude {r2.get('category')}")
            r2.setdefault("quantite", task.get("quantite",1)); r2.setdefault("skill_needed", r2.get("category","autre"))
            return r2
        # 3. Fallback heuristique (toujours dispo)
        h = self._heuristic(task)
        h["quantite"]=task.get("quantite",1); h["skill_needed"]=h["category"]
        return h

    def _heuristic(self, task: dict) -> dict[str, Any]:
        from agent.pieces import analyse_pieces
        from agent.geo import distance_from_bureau
        from agent.weather import get_meteo
        from agent.price_estimator import estimer_prix
        desc=(task.get("description","")+task.get("type","")).lower()
        if "crevaison" in desc or "pneu" in desc:
            cat="crevaison"; diff="facile"; duree=30; pieces=["chambre à air"]
        elif "frein" in desc:
            cat="frein"; diff="moyen"; duree=45; pieces=["patins/câble"]
        elif "chaine" in desc or "transmission" in desc or "vitesse" in desc:
            cat="transmission"; diff="moyen"; duree=60; pieces=["chaîne"]
        elif "electrique" in desc or "moteur" in desc or "batterie" in desc:
            cat="electrique"; diff="difficile"; duree=90; pieces=["diagnostic"]
        else:
            cat="autre"; diff="moyen"; duree=45; pieces=[]
        g = distance_from_bureau(task.get("adresse","Paris"))
        distance = g["distance_km"]
        meteo = get_meteo(g["lat"], g["lon"])
        proche = distance <= 12
        facile = diff=="facile" and proche
        urgence = "haute" if facile or cat=="crevaison" else "moyenne" if diff=="moyen" else "basse"
        confiance = 90 if cat in ["crevaison","frein"] and proche else 80 if proche else 60
        # enrichissement complet
        tmp = {"category": cat, "difficulte": diff, "duree_min": duree, "pieces": pieces, "distance_km": distance, "proche": proche, "facile": facile, "urgence": urgence, "confidence": confiance}
        prix = estimer_prix(task, tmp)
        pieces_info = analyse_pieces(task, cat)
        return {
            "task_id": task.get("id"), "category": cat, "difficulte": diff,
            "duree_min": duree, "pieces": pieces, "pieces_detail": pieces_info, "distance_km": distance,
            "meteo": meteo, "prix": prix, "charge": prix["charge"],
            "proche": proche, "facile": facile, "urgence": urgence, "confidence": confiance,
            "llm": "heuristic",
            "reason": f"{cat}/{diff} {distance}km {meteo['difficulte']} {prix['charge']['niveau']} → {'cargo OK' if proche else 'loin'} • {prix['garantie']}"
        }

if __name__=="__main__":
    import json
    lc=LLMChat()
    for t in [{"id":"REP-1","description":"crevaison Paris 18","adresse":"Paris 18"},{"id":"REP-2","description":"moteur électrique HS Paris 13","adresse":"Paris 13"}]:
        print(json.dumps(lc.analyze(t), indent=2, ensure_ascii=False))
