#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Any
import os

class WhatsApp:
    VERSION="0.1.0"
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config/config.yaml"
        p=Path(config_path)
        if not p.exists():
            p=Path(__file__).parent.parent / "config/config.example.yaml"
        import yaml
        self.config=yaml.safe_load(p.read_text()) if p.exists() else {}
        self.logs=[]

    def send(self, to: str, body: str, dry_run=True) -> dict[str,Any]:
        wa=self.config.get("whatsapp",{})
        provider=wa.get("provider","twilio")
        if dry_run or wa.get("account_sid","").startswith("env:") and not os.environ.get("TWILIO_SID"):
            self.logs.append({"to": to, "body": body, "dry_run": True, "provider": provider})
            print(f"[WhatsApp dry_run → {to}] {body}")
            return {"to": to, "status": "dry_run", "provider": provider}
        try:
            from twilio.rest import Client
            sid=os.environ.get(wa["account_sid"][4:]) if str(wa.get("account_sid")).startswith("env:") else wa.get("account_sid")
            tok=os.environ.get(wa["auth_token"][4:]) if str(wa.get("auth_token")).startswith("env:") else wa.get("auth_token")
            frm=wa.get("from","whatsapp:+14155238886")
            client=Client(sid,tok)
            msg=client.messages.create(from_=frm, to=f"whatsapp:{to}" if not to.startswith("whatsapp:") else to, body=body)
            return {"to": to, "status": "sent", "sid": msg.sid}
        except Exception as e:
            return {"to": to, "status": "error", "error": str(e)}

    def notify_assignment(self, task: dict, assign: dict, dry_run=True):
        wa=self.config.get("whatsapp",{})
        tmpl=wa.get("templates",{})
        # templates labes.pro utilisent {category} {difficulte} {distance_km}
        # aliases pour templates labes.pro
        ctx = {**task, **assign, "category": assign.get("category") or task.get("type"), "difficulte": assign.get("difficulte","facile"), "distance_km": assign.get("distance_km","?"), "duree_min": assign.get("duree_min",30), "pieces": ",".join(assign.get("pieces",[]))}
        ctx["tech_nom"] = ctx.get("technician","")
        ctx["tech"] = ctx.get("technician","")
        # assure adresse
        ctx.setdefault("adresse", task.get("adresse","Paris"))
        staff_tpl=tmpl.get("staff","🚲 Labès #{id} — {category} ({difficulte}) {distance_km}km {duree_min}min — {adresse} — Client {client_tel} — {pieces}")
        client_tpl=tmpl.get("client","✅ Labès — Votre demande #{id} ({category}) est prise en charge par {technician} (cargo vélo).")
        def safe_fmt(s, d):
            try: return s.format(**d)
            except: 
                try: return s.format_map({k: d.get(k,"") for k in d})
                except: return s
        staff_msg=safe_fmt(staff_tpl, ctx)
        client_msg=safe_fmt(client_tpl, ctx)
        staff_tel = "+33000000099"  # placeholder — configurer vrai numéro staff dans config.yaml
        return {
            "staff": self.send(staff_tel, staff_msg, dry_run=dry_run),
            "client": self.send(task.get("client_tel",""), client_msg, dry_run=dry_run)
        }

if __name__=="__main__":
    w=WhatsApp()
    print(w.notify_assignment({"id":"LOC-101","type":"velo_electrique","quantite":2,"date_debut":"2026-09-18","date_fin":"2026-09-20","lieu":"Paris","client_tel":"+33000000001"}, {"technician":"stock_ebike_1"}))
