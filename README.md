<p align="center">
  <img src="https://img.shields.io/badge/Agent_Bike-Location_Vélo-00C853?style=for-the-badge&logo=bike&logoColor=white" alt="Agent Bike"/>
  <img src="https://img.shields.io/badge/Paris-Aubervilliers_cargo-00D1FF?style=for-the-badge" alt="cargo"/>
  <img src="https://img.shields.io/badge/WhatsApp-auto-25D366?style=for-the-badge&logo=whatsapp&logoColor=white" alt="whatsapp"/>
  <img src="https://img.shields.io/badge/ChatGPT%2FClaude-branché-AA00FF?style=for-the-badge" alt="llm"/>
</p>

<h1 align="center">Agent Bike — Location & Réparation Vélo</h1>

<p align="center">
  <em>« Client demande vélo → Mon site l'attribue → WhatsApp gère »</em><br/>
  <strong>Agent Bike • Location & Réparation à domicile • Cargo Aubervilliers → Paris • 100% traçable</strong>
</p>

> ⚠️ **Agent Bike** pour **labes.pro** et tout site location/réparation vélo. Lit les demandes, attribue via ton site, gère WhatsApp + carte + prix fixe.

---

## 🗺️ Flux — Flèches

```mermaid
graph LR
    A[📥 Site<br/>Demande vélo] --> B[🔍 TaskReader<br/>API / Scrape]
    B --> C[🧠 LLM Analyzer<br/>type vélo + dates + quantite]
    C --> D[👤 Attributor<br/>stock via site API]
    D --> E[💬 WhatsApp<br/>notif staff + client]
    E --> F[🔄 Tracker<br/>statut → site]
    F --> G[✅ Confirmé]
    style C fill:#00D1FF,stroke:#000,stroke-width:2px
    style D fill:#FF6D00,stroke:#000,stroke-width:2px,color:#fff
    style E fill:#25D366,stroke:#000,stroke-width:2px,color:#fff
```

```
📥 Demande vélo site (LOC-xxx)
  → 🔍 TaskReader (poll /rentals ou webhook)
  → 🧠 LLM (velo_electrique/vtt/classique + urgence)
  → 👤 Attributor (POST /rentals/{id}/assign → stock)
  → 💬 WhatsApp (staff + client)
  → 🔄 Tracker (statut ↔ site ↔ WhatsApp)
```

---

## 📦 Structure (même méthode CyberAI)

```
repair-agent/
├── agent/
│   ├── task_reader.py      → lit tâches depuis ton site
│   ├── attributor.py       → attribue via API site
│   ├── whatsapp.py         → envoi/suivi WhatsApp
│   ├── llm_analyzer.py     → LLM + fallback déterministe
│   └── orchestrator.py     → 📁 → 🔍 → 🧠 → 👤 → 💬 → 🔄
├── config/
│   └── config.yaml         → URL site, tokens, mappings
├── assets/                 → banner, demo
└── tests/
```

**Principes (identique UniversalAgent) :**
- Isolation — chaque module testable seul
- LLM propose → déterministe dispose (pas d'attribution sans validation API)
- Traçabilité — chaque action loggée + écrite sur le site

---

## 🚀 Quickstart

```bash
git clone <repo> && cd repair-agent
pip install -r requirements.txt
cp config/config.example.yaml config/config.yaml  # renseigne URL site + tokens

# 1 tâche
PYTHONPATH=. python3 -m agent.orchestrator --once

# continu
PYTHONPATH=. python3 -m agent.orchestrator --loop

# API granulaire
PYTHONPATH=. python3 -m agent.task_reader --list
PYTHONPATH=. python3 -m agent.attributor --dry-run
PYTHONPATH=. python3 -m agent.whatsapp --test +213XXXXXXXX
```

---

## ⚙️ Config

```yaml
site:
  base_url: "https://ton-site.com/api"
  token: "env:SITE_TOKEN"
  endpoints:
    list: "/repairs?status=pending"
    assign: "/repairs/{id}/assign"
    status: "/repairs/{id}/status"

whatsapp:
  provider: "twilio" # ou whatsapp-business / baileys
  token: "env:WHATSAPP_TOKEN"
  templates:
    assign: "Nouvelle tâche #{id} : {type} à {adresse}"
    client: "Votre réparation #{id} est prise en charge par {tech}"
```

---

## 📊 Exemples — Vélo

| Demande client | → Attribution stock | → WhatsApp |
|---|---|---|
| 2 vélos électriques Alger 18-20 sept | → `stock_ebike_1` | `💬 Staff: nouvelle loc + client confirmé` |
| VTT Oran 1 jour | → `stock_vtt_1` | `💬 Devis auto + suivi` |
| 4 vélos classiques famille Constantine | → `stock_velo_1` | `💬 Famille notifiée` |

---

<p align="center"><strong>Malek Boucetta</strong> — même méthode que CyberAI, appliquée au terrain.</p>
