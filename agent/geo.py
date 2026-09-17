#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
import math, requests
from pathlib import Path

BUREAU = {"lat": 48.9147, "lon": 2.3844, "adresse": "Aubervilliers"}

# Cache simple
CACHE = Path("logs/geocache.json")
CACHE.parent.mkdir(exist_ok=True)

def haversine(lat1, lon1, lat2, lon2):
    R=6371
    dlat=math.radians(lat2-lat1); dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(a))

def geocode(adresse: str) -> dict[str, Any]:
    """Nominatim OSM — gratuit, pas de clé"""
    # cache
    import json
    cache={}
    if CACHE.exists():
        try: cache=json.loads(CACHE.read_text())
        except: cache={}
    if adresse in cache:
        return cache[adresse]
    try:
        # Toujours Paris, France — évite homonymes (Paris, Vietnam : vu)
        base_q = adresse if "paris" in adresse.lower() else adresse + ", Paris"
        q = base_q + ", France" if "france" not in base_q.lower() else base_q
        # Biais Paris Île-de-France + countrycodes fr
        r=requests.get("https://nominatim.openstreetmap.org/search", params={"q": q, "format":"json","limit":1, "countrycodes":"fr", "viewbox":"2.2,48.95,2.5,48.80", "bounded":1}, headers={"User-Agent":"Agent Bike/0.2"}, timeout=10)
        r.raise_for_status()
        data=r.json()
        if data:
            res={"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"]), "display": data[0]["display_name"]}
            cache[adresse]=res
            CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))
            return res
    except Exception as e:
        pass
    # fallback arrondissement
    import re
    m=re.search(r"750(\d{2})", adresse)
    if m:
        arr=int(m.group(1))
        # approx centre arrondissement
        approx={75018:(48.892,2.344),75019:(48.883,2.382),75010:(48.877,2.36),75013:(48.832,2.355)}.get(int("750"+m.group(1)), (48.8566,2.3522))
        return {"lat": approx[0], "lon": approx[1], "display": f"Paris {arr} (approx)"}
    return {"lat": 48.8566, "lon": 2.3522, "display": "Paris centre (fallback)"}

def distance_from_bureau(adresse: str) -> dict:
    g=geocode(adresse)
    d=haversine(BUREAU["lat"], BUREAU["lon"], g["lat"], g["lon"])
    return {"adresse": adresse, **g, "distance_km": round(d,2), "bureau": BUREAU, "cargo_ok": d<=12, "duree_velo_min": round(d/15*60)}  # 15km/h cargo

def link_tasks(tasks: list[dict]) -> dict:
    """Relie les tâches par proximité — clusters pour tournée cargo"""
    for t in tasks:
        geo=distance_from_bureau(t.get("adresse","Paris"))
        t["_geo"]=geo
    # tri par distance depuis Aubervilliers (tournée)
    ordered=sorted(tasks, key=lambda x: x["_geo"]["distance_km"])
    # clusters proches (<3km entre eux)
    clusters=[]
    for t in ordered:
        placed=False
        for c in clusters:
            if haversine(t["_geo"]["lat"], t["_geo"]["lon"], c[0]["_geo"]["lat"], c[0]["_geo"]["lon"]) < 3:
                c.append(t); placed=True; break
        if not placed:
            clusters.append([t])
    total_km=sum(t["_geo"]["distance_km"] for t in ordered)
    return {"ordered": ordered, "clusters": clusters, "total_km": round(total_km,2), "bureau": BUREAU}

def generate_map(tasks: list[dict], out="assets/map.html"):
    """Génère map Leaflet autonome"""
    linked=link_tasks(tasks)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    markers=""
    for t in linked["ordered"]:
        g=t["_geo"]
        markers+=f"""
  L.marker([{g['lat']}, {g['lon']}]).addTo(map)
    .bindPopup("<b>{t['id']}</b><br>{t.get('type','')} — {t.get('description','')}<br>{g['adresse']}<br>{g['distance_km']}km • {g['duree_velo_min']}min cargo");
"""
    html=f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Agent Bike Map — Aubervilliers → Paris</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#map{{height:100%;margin:0}} .badge{{position:absolute;top:10px;left:50%;transform:translateX(-50%);background:white;padding:8px 14px;border-radius:20px;box-shadow:0 2px 8px rgba(0,0,0,.2);z-index:1000;font-family:sans-serif}}</style>
</head><body>
<div class="badge">🚲 Bureau Aubervilliers → {len(tasks)} tâches Paris • {linked['total_km']}km total • {len(linked['clusters'])} clusters</div>
<div id="map"></div>
<script>
var map = L.map('map').setView([{BUREAU['lat']}, {BUREAU['lon']}], 12);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{attribution:'© OSM'}}).addTo(map);
L.marker([{BUREAU['lat']}, {BUREAU['lon']}]).addTo(map).bindPopup("<b>🏠 Bureau Aubervilliers</b><br>Base cargo vélo").openPopup();
{markers}
var latlngs = [[{BUREAU['lat']}, {BUREAU['lon']}]];
linked = {str([[t['_geo']['lat'], t['_geo']['lon']] for t in linked['ordered']])};
latlngs = latlngs.concat(linked);
L.polyline(latlngs, {{color:'#00C853', weight:4, opacity:.7, dashArray:'8,8'}}).addTo(map);
</script></body></html>"""
    Path(out).write_text(html, encoding="utf-8")
    return {"map": out, "linked": linked}

if __name__=="__main__":
    import json
    tasks=[{{"id":"REP-1","adresse":"Paris 18","type":"crevaison"}},{{"id":"REP-2","adresse":"Paris 13","type":"frein"}}]
    print(generate_map(tasks))
