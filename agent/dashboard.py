#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import json

from agent.task_reader import TaskReader
from agent.llm_chat import LLMChat
from agent.geo import link_tasks, generate_map, BUREAU

app = FastAPI(title="RepairFlow Dashboard", version="0.2")

# mécaniciens (exemple Aubervilliers cargo)
MECANOS = [
    {"id": "m1", "nom": "Malek", "velo": "Cargo Bullitt", "zone": "Nord Paris (18/19/10)", "status": "dispo", "tel": "+213550000010"},
    {"id": "m2", "nom": "Yacine", "velo": "Cargo Long John", "zone": "Centre (1/2/9/11)", "status": "en tournée", "tel": "+213550000011"},
    {"id": "m3", "nom": "Sara", "velo": "Cargo E-Bullitt", "zone": "Sud (13/15)", "status": "dispo", "tel": "+213550000012"},
]

@app.get("/api/tasks")
def api_tasks():
    tr=TaskReader(); tasks=tr.list_tasks()
    lc=LLMChat()
    for t in tasks:
        if "_error" not in t:
            t["_analyse"]=lc.analyze(t)
    linked=link_tasks([t for t in tasks if "_error" not in t])
    return {"bureau": BUREAU, "mecaniciens": MECANOS, **linked}

@app.get("/api/mecaniciens")
def api_mecanos():
    return MECANOS

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    html = Path("assets/dashboard.html")
    if html.exists():
        return html.read_text(encoding="utf-8")
    # fallback généré
    return HTMLResponse(_dashboard_html())

def _dashboard_html():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>RepairFlow — Dashboard Pro</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{box-sizing:border-box;font-family:Inter,system-ui,sans-serif}
body{margin:0;background:#f6f7f9}
header{background:#111;color:white;padding:14px 20px;display:flex;justify-content:space-between;align-items:center}
.badge{background:#00C853;color:white;padding:6px 12px;border-radius:20px;font-weight:600}
.grid{display:grid;grid-template-columns:1fr 360px;gap:16px;padding:16px}
.card{background:white;border-radius:14px;box-shadow:0 4px 16px rgba(0,0,0,.08);padding:16px}
#map{height:520px;border-radius:12px}
.mecano{display:flex;justify-content:space-between;align-items:center;padding:10px;border:1px solid #eee;border-radius:10px;margin:8px 0}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block}
.task{padding:10px;border-left:4px solid #00C853;background:#f9f9f9;margin:8px 0;border-radius:8px}
</style></head><body>
<header><div><b>🚲 RepairFlow</b> — Aubervilliers → Paris • Cargo vélo domicile</div><div class="badge">LIVE</div></header>
<div class="grid">
  <div class="card">
    <h3>🗺️ Carte tournée</h3>
    <div id="map"></div>
    <div id="stats" style="margin-top:10px;color:#666"></div>
  </div>
  <div>
    <div class="card">
      <h3>👨‍🔧 Mécaniciens</h3>
      <div id="mecs"></div>
    </div>
    <div class="card" style="margin-top:16px">
      <h3>📥 Demandes</h3>
      <div id="tasks"></div>
    </div>
  </div>
</div>
<script>
async function load(){
  let r=await fetch('/api/tasks'); let j=await r.json();
  document.getElementById('stats').innerText = `Bureau ${j.bureau.adresse} → ${j.ordered.length} tâches • ${j.total_km}km total • ${j.clusters.length} clusters`;
  let map=L.map('map').setView([48.9147,2.3844],12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OSM'}).addTo(map);
  L.marker([48.9147,2.3844]).addTo(map).bindPopup('<b>🏠 Bureau Aubervilliers</b><br>Base cargo').openPopup();
  let latlngs=[[48.9147,2.3844]];
  j.ordered.forEach(t=>{
    let g=t._geo;
    L.marker([g.lat,g.lon]).addTo(map).bindPopup(`<b>${t.id}</b><br>${t.type} — ${t.description||''}<br>${g.adresse}<br>${g.distance_km}km • ${g.duree_velo_min}min`);
    latlngs.push([g.lat,g.lon]);
  });
  L.polyline(latlngs,{color:'#00C853',weight:4,opacity:.7,dashArray:'8,8'}).addTo(map);
  document.getElementById('mecs').innerHTML = j.mecaniciens.map(m=>`
    <div class="mecano"><div><b>${m.nom}</b> — ${m.velo}<br><small>${m.zone}</small></div>
    <span><span class="dot" style="background:${m.status=='dispo'?'#00C853':'#FF6D00'}"></span> ${m.status}</span></div>
  `).join('');
  document.getElementById('tasks').innerHTML = j.ordered.map(t=>`
    <div class="task" style="border-color:${t._analyse.difficulte=='facile'?'#00C853': t._analyse.difficulte=='moyen'?'#FF6D00':'#D32F2F'}">
      <b>${t.id}</b> — ${t.type} x${t.quantite||1}<br>
      ${t.adresse} — ${t._analyse.difficulte} • ${t._analyse.duree_min}min • ${t._geo.distance_km}km<br>
      <small>${t._analyse.reason}</small>
      <div style="margin-top:6px"><span style="background:${t._geo.cargo_ok?'#E8F5E9':'#FFEBEE'};padding:4px 8px;border-radius:12px;font-size:12px">${t._geo.cargo_ok?'🚲 cargo OK':'⚠️ loin'}</span></div>
    </div>
  `).join('');
}
load();
</script></body></html>"""

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
