#!/usr/bin/env python3
from __future__ import annotations
from typing import Any

# Base labes.pro + stock Aubervilliers
PIECES_CATALOG = {
    "crevaison": {"pieces": ["chambre à air"], "stock": True, "urgent": True, "prix_piece": 8, "poids_kg": 0.2},
    "frein": {"pieces": ["patins", "câble"], "stock": True, "urgent": True, "prix_piece": 12, "poids_kg": 0.3},
    "transmission": {"pieces": ["chaîne", "dérailleur"], "stock": True, "urgent": False, "prix_piece": 25, "poids_kg": 0.5},
    "roue": {"pieces": ["rayons", "déroueur"], "stock": False, "urgent": False, "prix_piece": 30, "poids_kg": 1.2},
    "electrique": {"pieces": ["diagnostic Bosch/Bafang"], "stock": True, "urgent": False, "prix_piece": 0, "poids_kg": 0.1},
    "autre": {"pieces": [], "stock": True, "urgent": False, "prix_piece": 0, "poids_kg": 0},
}

def analyse_pieces(task: dict, category: str) -> dict[str, Any]:
    cat = PIECES_CATALOG.get(category, PIECES_CATALOG["autre"])
    desc = (task.get("description","")+task.get("panne","")).lower()
    urgent = cat["urgent"] or "urgent" in desc or "vite" in desc
    stock_ok = cat["stock"]
    # Si VAE et batterie/moteur -> pièce à commander (pas urgent, devis)
    if category=="electrique" and "batterie" in desc:
        stock_ok=False
    return {
        "pieces": cat["pieces"],
        "stock_ok": stock_ok,
        "urgent": urgent,
        "prix_piece_estime": cat["prix_piece"],
        "poids_kg": cat["poids_kg"],
        "conseil": "Pièce en stock Aubervilliers → cargo OK" if stock_ok else "Pièce à commander → 2e passage prévu"
    }
