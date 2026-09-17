#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Any
import os, yaml, json

class WhatsApp:
    VERSION="0.1.0"
    def __init__(self, config_path="config/config.yaml"):
        p=Path(config_path)
        if not p.exists():
            p=Path("config/config.example.yaml")
        self.config=yaml.safe_load(p.read_text()) if p.exists() else {}
        self.logs=[]

    def send(self, to: str, body: str, dry_run=True) -> dict[str,Any]:
        # dry_run par défaut — passe à False quand Twilio configuré
        wa=self.config.get("whatsapp",{})
        provider=wa.get("provider","twilio")
        if dry_run or wa.get("account_sid","").startswith("env:") and not os.environ.get("TWILIO_SID"):
            self.logs.append({"to": to, "body": body, "dry_run": True, "provider": provider})
            print(f"[WhatsApp dry_run → {to}] {body}")
            return {"to": to, "status": "dry_run", "provider": provider}
        # Twilio réel
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
        tech_msg=tmpl.get("technicien","🔧 Nouvelle tâche #{id} — {type} à {adresse}").format(id=task["id"], type=task.get("type"), adresse=task.get("adresse"), client_tel=task.get("client_tel"), urgence=task.get("urgence"))
        client_msg=tmpl.get("client","✅ Votre demande #{id} est prise en charge").format(id=task["id"], type=task.get("type"), tech_nom=assign.get("technician"))
        # map technicien → tel (à renseigner dans config)
        tech_tel = "+213550000099"  # placeholder
        return {
            "tech": self.send(tech_tel, tech_msg, dry_run=dry_run),
            "client": self.send(task.get("client_tel",""), client_msg, dry_run=dry_run)
        }

if __name__=="__main__":
    w=WhatsApp()
    print(w.notify_assignment({"id":"REP-101","type":"plomberie","adresse":"Alger","client_tel":"+213550000001","urgence":"haute"}, {"technician":"tech_plombier_1"}))
