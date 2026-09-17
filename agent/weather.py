#!/usr/bin/env python3
from __future__ import annotations
import requests, os
from pathlib import Path
import json

CACHE = Path("logs/weather.json")
CACHE.parent.mkdir(exist_ok=True)

def get_meteo(lat=48.9147, lon=2.3844) -> dict:
    """Open-Meteo gratuit sans clé — fallback heuristique"""
    try:
        r=requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,precipitation,wind_speed_10m",
            "forecast_days": 1
        }, timeout=10)
        r.raise_for_status()
        d=r.json()
        cur=d.get("current",{})
        temp=cur.get("temperature_2m", 15)
        precip=cur.get("precipitation", 0)
        wind=cur.get("wind_speed_10m", 10)
        # difficulté météo pour cargo
        if precip > 5:
            diff="difficile"; conseil="Pluie forte → bâche + temps +15min"
        elif precip > 0.5:
            diff="moyen"; conseil="Pluie légère → prévoir"
        elif wind > 30:
            diff="moyen"; conseil="Vent fort → charge lourde sensible"
        elif temp < 5:
            diff="moyen"; conseil="Froid → gants"
        else:
            diff="facile"; conseil="Météo OK"
        return {"temp": temp, "precip": precip, "vent": wind, "difficulte": diff, "conseil": conseil, "source": "open-meteo"}
    except Exception as e:
        # fallback heuristique Paris septembre
        return {"temp": 18, "precip": 0, "vent": 12, "difficulte": "facile", "conseil": "Météo estimée clémente (fallback)", "source": "heuristic"}

if __name__=="__main__":
    import json
    print(json.dumps(get_meteo(), indent=2, ensure_ascii=False))
