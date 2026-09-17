#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from agent.pieces import analyse_pieces
from agent.geo import distance_from_bureau
from agent.weather import get_meteo

TARIFS_LABES = {"facile": 15, "moyen": 30, "electrique": 50, "difficile": 50}

def estimer_prix(task: dict, analyse: dict) -> dict[str, Any]:
    cat = analyse.get("category","autre")
    difficulte = analyse.get("difficulte","moyen")
    # Tarif base labes.pro selon catégorie
    if cat in ["crevaison"]:
        base = TARIFS_LABES["facile"]
        niveau="facile"
    elif cat in ["frein","transmission","roue"]:
        base = TARIFS_LABES["moyen"]
        niveau="moyen"
    elif cat in ["electrique"]:
        base = TARIFS_LABES["electrique"]
        niveau="electrique"
    else:
        base = TARIFS_LABES["moyen"]
        niveau="moyen"

    pieces = analyse_pieces(task, cat)
    g = distance_from_bureau(task.get("adresse","Paris"))
    meteo = get_meteo(g["lat"], g["lon"])

    # Facteurs charge cargo
    quantite = task.get("quantite",1)
    poids = pieces["poids_kg"] * quantite
    charge = "leger" if poids < 1 else "moyen" if poids < 5 else "lourd"

    # Difficulté globale
    facteurs=[]
    if g["distance_km"] > 10: facteurs.append("distance longue")
    if meteo["difficulte"] != "facile": facteurs.append(f"météo {meteo['difficulte']}")
    if charge=="lourd": facteurs.append("charge lourde")
    if difficulte=="difficile": facteurs.append("panne difficile")
    if not pieces["stock_ok"]: facteurs.append("pièce à commander")

    # Prix estimé: base + pièces (mais plafonné pour client)
    prix_piece = pieces["prix_piece_estime"]
    # Si pièce à commander, on ne la facture pas dans l'estimé (devis sur place)
    if not pieces["stock_ok"]:
        prix_piece = 0
        note_piece = "Pièce à commander — devis sur place, prix main-d'œuvre fixe"
    else:
        note_piece = f"Pièce estimée {prix_piece}€ — confirmée sur place avant commande"

    prix_estime = base  # main-d'œuvre fixe labes.pro
    prix_max = base  # jamais dépasse pour main-d'œuvre
    # Garantie labes.pro: prix fixe annoncé avant
    garantie = f"Prix main-d'œuvre FIXE {base}€ — ne bougera jamais (pièces en sus {note_piece.lower()})"

    return {
        "base_mo": base,
        "niveau": niveau,
        "prix_estime_mo": prix_estime,
        "prix_max_mo": prix_max,
        "prix_piece_estime": prix_piece,
        "garantie": garantie,
        "facteurs": facteurs,
        "difficulte_globale": "difficile" if len(facteurs)>=3 else "moyen" if facteurs else "facile",
        "meteo": meteo,
        "distance": g,
        "charge": {"poids_kg": poids, "niveau": charge},
        "pieces": pieces,
        "affichage": f"{base}€ MO + {prix_piece}€ pièces ({pieces['pieces'][0] if pieces['pieces'] else 'aucune'}) — {garantie}"
    }

if __name__=="__main__":
    import json
    t={"id":"LAB-101","type":"crevaison","description":"crevaison","adresse":"18 rue de Clignancourt, Paris 75018","quantite":1}
    a={"category":"crevaison","difficulte":"facile"}
    print(json.dumps(estimer_prix(t,a), indent=2, ensure_ascii=False))
