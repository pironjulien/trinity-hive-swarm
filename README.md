# 🐝 TRINITY HIVE SWARM — Cookie-Based Gemini Parallelization

**Status:** Proof of Concept  
**Architecture:** Redis + FastAPI + Agentic Workers (Cookie Injection)  
**Author:** Julien Piron / Trinity Hackathon (2026)  
**License:** MIT

---

## What This Proves

This project demonstrates **client-side agentic swarm orchestration**. By networking multiple instances of a local Agentic IDE (like Antigravity) running on the same machine, Trinity transforms legitimate, consumer-grade user tools into an industrial, parallelized API.

### The Concept

Google's Gemini web interface is free for personal use. A **Google AI Family Sharing** subscription allows 6 family members to have distinct access.
Instead of using headless scrapers that get easily flagged and blocked, Trinity connects each of the 6 Google accounts to a separate, local instance of an **Agentic IDE (Antigravity)**. She then uses a local Redis instance to orchestrate tasks across all 6 profiles.

The result: **N workers = N× throughput**, running entirely on authorized local environments.

### Why It's Devastating (The Insidious Nature of Local Swarms)

This is the hardest route for Google to block because the traffic is fundamentally legitimate. To Google's servers, this looks exactly like a family of developers working on their respective machines using authorized Agentic IDEs.
To prevent this attack vector, Google would have to forbid Agentic IDEs from using session cookies entirely, or dismantle the Family Sharing system.

### Key Features
- **Legitimate Network Signature** — Traffic comes from authorized Agentic IDEs, not headless bots.
- **Free Parallelism** — 6 concurrent workers by default via Family Sharing.
- **Total Isolation** — Secondary account sessions keep the main account clean.
- **Agentic Workers** — Each worker is a full IDE instance with filesystem tools.
- **Local Swarm Orchestration** — Redis coordinates the independent local agents.

## Architecture

```text
┌─────────────────┐       ┌──────────┐       ┌────────────────────────┐
│  mission.py     │──────▶│  Redis   │──────▶│ Antigravity Profile 1  │──▶ Cookie A (Family 1)
│  (Swarm Leader) │       │  Queue   │       │ Antigravity Profile 2  │──▶ Cookie B (Family 2)
│                 │       │ (Local)  │       │ Antigravity Profile 3  │──▶ Cookie C (Family 3)
│                 │       │          │       │ Antigravity Profile 4  │──▶ Cookie D (Family 4)
└─────────────────┘       └──────────┘       └────────────────────────┘
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure cookies:** Copy `.env.example` to `.env` and populate with secondary account cookies (from browser DevTools → Application → Cookies on gemini.google.com).

3. **Install Redis:** Download [Redis for Windows](https://github.com/microsoftarchive/redis/releases) and place binaries in `redis/` directory, or use Docker: `docker run -d -p 6379:6379 redis`.

4. **Launch a mission:**
   ```bash
   python core/mission.py "Your mission here"
   ```

5. **Result:** The script starts Redis, spawns workers, injects the task, and the result lands in `output/`.

## File Structure

```
/
├── LICENSE               # MIT License
├── DISCLAIMER.md         # Educational PoC disclaimer
├── README.md             # This file
├── .env.example          # Cookie template (no secrets)
├── requirements.txt      # Python dependencies (pinned)
├── core/
│   ├── mission.py        # Orchestrator (Redis + N Workers)
│   ├── worker_v2.py      # Agentic worker (cookie-based Gemini client)
│   └── toolkit.py        # Filesystem tools (read, write, list, exec)
├── api/
│   └── main.py           # FastAPI gateway (launch, status, queue)
└── missions/
    └── mission_template_v2.json  # Task template
```

## Security

- `.env` is gitignored — cookies are never committed
- Workers use **secondary account** cookies only
- Redis runs locally — no external exposure

---
*Trinity Hackathon 2026 — Technical Demonstration*
