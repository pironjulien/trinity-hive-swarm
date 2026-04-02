# 🐝 TRINITY HIVE SWARM — Cookie-Based Gemini Parallelization

**Status:** Proof of Concept  
**Architecture:** Redis + FastAPI + Workers V2 (Cookie Injection)  
**Author:** Julien Piron / Trinity Hackathon (2026)

---

## What This Proves

This project demonstrates **massive parallelization of a free AI web interface** by injecting secondary account cookies into headless workers, effectively turning a consumer-grade chatbot into an industrial API.

### Key Concepts
- **Free Parallelism:** 4 concurrent workers by default (scalable to 10+)
- **Total Isolation:** Secondary account cookies keep your main account clean
- **Zero API Cost:** No AI Studio or Vertex AI keys required
- **Autonomous Workers:** Each worker has filesystem tools (read, write, exec)

## Architecture

```
┌─────────────┐     ┌──────────┐     ┌──────────────┐
│  mission.py │────▶│  Redis   │────▶│ Worker V2 #1 │──▶ Cookie A
│ Orchestrator│     │  Queue   │     │ Worker V2 #2 │──▶ Cookie B
│             │     │          │     │ Worker V2 #3 │──▶ Cookie C
│             │     │          │     │ Worker V2 #4 │──▶ Cookie D
└─────────────┘     └──────────┘     └──────────────┘
                         │
                  ┌──────┴──────┐
                  │ FastAPI GW  │
                  │   :8000     │
                  └─────────────┘
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure cookies:** Copy `.env.example` to `.env` and populate with secondary account cookies.

3. **Install Redis:** Download [Redis for Windows](https://github.com/microsoftarchive/redis/releases) and place binaries in `redis/` directory.

4. **Launch a mission:**
   ```bash
   python core/mission.py "Your mission here"
   ```

5. **Result:** The script starts Redis, spawns workers, injects the task, and the result lands in `output/`.

## File Structure

```
/
├── .env.example          # Cookie template (no secrets)
├── requirements.txt      # Python dependencies
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
