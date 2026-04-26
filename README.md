# 🐝 TRINITY HIVE SWARM — Cookie-Based Gemini Parallelization

**Status:** Proof of Concept  
**Architecture:** Redis + FastAPI + Agentic Workers (Cookie Injection)  
**Author:** Julien Piron / Trinity Hackathon (2026)  
**License:** MIT

---

## What This Proves

This project demonstrates **massive parallelization of a free AI web interface** by injecting secondary account cookies into headless workers, effectively turning a consumer-grade chatbot into an industrial API.

### The Concept

Google's Gemini web interface is free for personal use, rate-limited per-account. By leveraging **Google Family Sharing** mechanics — where each family member is a separate Google account — we create a swarm of parallel workers, each authenticated with a distinct secondary account cookie.

The result: **N workers = N× throughput**, with zero API billing.

### Why It's Devastating

This is the hardest route for Google to block. To prevent this attack vector, Google would have to fundamentally rethink how Family Sharing and multi-account sessions work — changes that would impact **every Google service**, not just Gemini.

### Key Features
- **Free Parallelism** — 4 concurrent workers by default (scalable to N+)
- **Total Isolation** — secondary account cookies keep your main account clean
- **Zero API Cost** — no AI Studio or Vertex AI keys required
- **Agentic Workers** — each worker has filesystem tools (read, write, list_dir, exec)
- **Mission System** — JSON-based task dispatch via Redis queue
- **FastAPI Gateway** — REST API for task submission and status monitoring

## Architecture

```
┌─────────────┐     ┌──────────┐     ┌──────────────┐
│  mission.py │────▶│  Redis   │────▶│ Worker V2 #1 │──▶ Cookie A (Family Member 1)
│ Orchestrator│     │  Queue   │     │ Worker V2 #2 │──▶ Cookie B (Family Member 2)
│             │     │          │     │ Worker V2 #3 │──▶ Cookie C (Family Member 3)
│             │     │          │     │ Worker V2 #4 │──▶ Cookie D (Family Member 4)
└─────────────┘     └──────────┘     └──────────────┘
                         │
                  ┌──────┴──────┐
                  │ FastAPI GW  │
                  │   :8000     │
                  └─────────────┘
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
