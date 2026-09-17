#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, time, argparse

from agent.task_reader import TaskReader
from agent.llm_analyzer import LLMAnalyzer
from agent.attributor import Attributor
from agent.whatsapp import WhatsApp

def run_once(dry_run=True, config="config/config.yaml"):
    tr=TaskReader(config); an=LLMAnalyzer(); at=Attributor(config); wa=WhatsApp(config)
    tasks=tr.list_tasks()
    print(f"[+] {len(tasks)} tâche(s) lue(s) depuis site")
    results=[]
    for t in tasks:
        if "_error" in t:
            print(f"[!] {t}"); continue
        print(f"\n── {t['id']} — {t['type']} @ {t['adresse']} ──")
        analysis=an.analyze(t)
        print(f"  🧠 {analysis['category']} / {analysis['urgence']} ({analysis['confidence']}%) → {analysis['reason']}")
        assign=at.assign(t, analysis, dry_run=dry_run)
        print(f"  👤 → {assign['technician']} validated={assign['validated']} dry_run={assign.get('dry_run')}")
        if not assign["validated"]:
            print("  ❌ attribution rejetée (validator)")
            results.append({"task":t,"analysis":analysis,"assign":assign,"status":"REJECTED"})
            continue
        notif=wa.notify_assignment(t, assign, dry_run=dry_run)
        print(f"  💬 WhatsApp tech={notif['tech']['status']} client={notif['client']['status']}")
        results.append({"task":t,"analysis":analysis,"assign":assign,"notif":notif,"status":"DISPATCHED"})
    # log
    Path("logs").mkdir(exist_ok=True)
    Path("logs/last_run.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n[+] Log → logs/last_run.json ({len(results)} résultats)")
    return results

def main():
    p=argparse.ArgumentParser(description="RepairFlow Orchestrator")
    p.add_argument("--once", action="store_true", help="une passe")
    p.add_argument("--loop", action="store_true", help="poll continu")
    p.add_argument("--dry-run", action="store_true", default=True, help="n'écrit pas vraiment sur site/WhatsApp")
    p.add_argument("--live", action="store_true", help="écriture réelle (annule dry-run)")
    p.add_argument("--config", default="config/config.yaml")
    args=p.parse_args()
    dry = not args.live
    if args.loop:
        interval=60
        try:
            from pathlib import Path as _P
            import yaml as _y
            if _P(args.config).exists():
                interval=_y.safe_load(_P(args.config).read_text()).get("site",{}).get("poll_interval",60)
        except: pass
        print(f"[loop] poll {interval}s — Ctrl+C pour stop")
        while True:
            run_once(dry_run=dry, config=args.config)
            time.sleep(interval)
    else:
        run_once(dry_run=dry, config=args.config)

if __name__=="__main__":
    main()
