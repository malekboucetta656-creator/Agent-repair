#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, time, argparse

from agent.task_reader import TaskReader
from agent.llm_analyzer import LLMAnalyzer
from agent.attributor import Attributor
from agent.whatsapp import WhatsApp

def run_once(dry_run=True, config=None):
    tr=TaskReader(config); an=LLMAnalyzer(); at=Attributor(config); wa=WhatsApp(config)
    tasks=tr.list_tasks()
    print(f"[+] {len(tasks)} demande(s) location vélo lue(s) depuis site")
    results=[]
    for t in tasks:
        if "_error" in t:
            print(f"[!] {t}"); continue
        print(f"\n── {t['id']} — {t['type']} x{t.get('quantite',1)} {t.get('date_debut','')}→{t.get('date_fin','')} @ {t.get('lieu', t.get('adresse','Paris'))} ──")
        analysis=an.analyze(t)
        print(f"  🧠 {analysis['category']} x{analysis.get('quantite', t.get('quantite',1))} / {analysis['urgence']} ({analysis['confidence']}%) → {analysis['reason']} [{analysis.get('llm','heuristic')}] distance {analysis.get('distance_km','?')}km")
        assign=at.assign(t, analysis, dry_run=dry_run)
        # enrich assign avec analyse pour WhatsApp/map
        assign.update({k: analysis.get(k) for k in ["category","difficulte","distance_km","duree_min","pieces"] if k in analysis})
        print(f"  👤 → {assign['technician']} validated={assign['validated']} dry_run={assign.get('dry_run')} tarif {analysis.get('duree_min')}min")
        if not assign["validated"]:
            print("  ❌ stock invalide (validator)")
            results.append({"task":t,"analysis":analysis,"assign":assign,"status":"REJECTED"})
            continue
        notif=wa.notify_assignment(t, assign, dry_run=dry_run)
        print(f"  💬 WhatsApp staff={notif['staff']['status']} client={notif['client']['status']}")
        results.append({"task":t,"analysis":analysis,"assign":assign,"notif":notif,"status":"DISPATCHED"})
    Path("logs").mkdir(exist_ok=True)
    Path("logs/last_run.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n[+] Log → logs/last_run.json ({len(results)} résultats)")
    return results

def main():
    p=argparse.ArgumentParser(description="Agent Bike — Location Vélo Orchestrator")
    p.add_argument("--once", action="store_true", help="une passe")
    p.add_argument("--loop", action="store_true", help="poll continu")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--live", action="store_true", help="écriture réelle")
    p.add_argument("--config", default=None)
    args=p.parse_args()
    dry = not args.live
    if args.loop:
        interval=60
        try:
            import yaml
            cfg = Path(args.config) if args.config else Path(__file__).parent.parent / "config/config.yaml"
            if not cfg.exists():
                cfg = Path(__file__).parent.parent / "config/config.example.yaml"
            interval=yaml.safe_load(cfg.read_text()).get("site",{}).get("poll_interval",60)
        except: pass
        print(f"[loop] poll {interval}s — Ctrl+C pour stop")
        while True:
            run_once(dry_run=dry, config=args.config)
            time.sleep(interval)
    else:
        run_once(dry_run=dry, config=args.config)

if __name__=="__main__":
    main()
