# 🐝 TRINITY HIVE SWARM — Local Agentic Swarm (Cookie Injection)

**Status:** Proof of Concept  
**Architecture:** Single Local IDE + Redis Orchestrator + 6 Parallel Sessions  
**Author:** Julien Piron / Trinity Hackathon (2026)  
**License:** MIT

---

## What This Proves

This project demonstrates **client-side agentic swarm orchestration within a single IDE session**. By injecting multiple secondary account cookies into a single local Agentic IDE (like Antigravity), Trinity transforms a legitimate user tool into an industrial, parallelized API, completely bypassing standard rate limits.

### The Concept

Google's Gemini web interface is free for personal use. A **Google AI Family Sharing** subscription allows 6 family members to have distinct access.
Instead of using headless scrapers or opening 6 different IDEs, Trinity extracts the session cookies from all 6 accounts and injects them into a **single local Antigravity IDE instance**. 
When faced with massive generation tasks, the IDE acts as a "Swarm Leader", round-robining or parallelizing requests across the 6 authenticated sessions simultaneously.

The result: **1 Developer = 6× throughput**, running entirely within a single, authorized local environment.

### Why It's Devastating (The Insidious Nature of Local Swarms)

This is the hardest route for Google to block because the traffic is fundamentally legitimate. To Google's servers, this looks like normal web traffic originating from an authorized Agentic IDE. The parallelization happens invisibly at the client level.
To prevent this attack vector, Google would have to forbid Agentic IDEs from using session cookies entirely, or dismantle the Family Sharing system.

### Key Features
- **Legitimate Network Signature** — Traffic comes from an authorized Agentic IDE client.
- **Free Parallelism** — 6 concurrent API channels via Family Sharing in a single app.
- **Total Isolation** — Secondary account sessions keep the main account clean.
- **Single-Node Swarm Orchestration** — A local script (or Redis) coordinates the independent cookies within the same IDE instance.

## Architecture

```text
┌──────────────────────────────────────────────┐
│  Antigravity IDE (Single Local Instance)     │
│                                              │
│  ┌────────────┐       ┌─────────────────┐    │
│  │ Swarm      │──────▶│ Cookie Injector │    │
│  │ Orchestrator│       └─────────────────┘    │
│  └────────────┘                 │            │
│         │                       ▼            │
│         │               [ HTTP Client ]      │
│         │                 /    |    \        │
└─────────┼────────────────┼─────┼─────┼───────┘
          │                │     │     │
          ▼                ▼     ▼     ▼
    Local Filesystem      C1    C2    C3 ... (6 Google Accounts via Family Sharing)
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
