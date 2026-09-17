from agent.task_reader import TaskReader
from agent.llm_analyzer import LLMAnalyzer
from agent.attributor import Attributor
from agent.whatsapp import WhatsApp

def test_velo_flow():
    tr = TaskReader()
    tasks = tr.list_tasks()
    assert len(tasks) >= 1
    assert tasks[0]["id"].startswith("REP-") or tasks[0]["id"].startswith("LOC-")
    an = LLMAnalyzer()
    at = Attributor()
    wa = WhatsApp()
    for t in tasks:
        a = an.analyze(t)
        assert a["category"] in ["crevaison","frein","transmission","electrique","autre","velo_electrique","vtt","velo_classique"]
        assign = at.assign(t, a, dry_run=True)
        assert "technician" in assign
        notif = wa.notify_assignment(t, assign, dry_run=True)
        assert notif["staff"]["status"] == "dry_run"
        assert notif["client"]["status"] == "dry_run"

if __name__ == "__main__":
    test_velo_flow()
    print("✅ tests velo pass")
