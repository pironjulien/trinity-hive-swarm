# 🐝 TRINITY HIVE SWARM — Local Agentic MoE Swarm (Cookie Injection)

**Status:** Proof of Concept  
**Architecture:** Fan-Out / Fan-In / Mixture of Experts (MoE) Synthesis  
**Author:** Julien Piron / Trinity Hackathon (2026)  
**License:** MIT

---

## What This Proves

This project demonstrates how a **single local IDE session** can be turned into an **industrial-scale, parallelized AI swarm** by injecting multiple Family Sharing account cookies into a single Agentic IDE (Antigravity).

Unlike Routes 1 (Discovery Engine) and 2 (Dialogflow CX) which exploit **Cloud API misconfigurations**, this route exploits the **consumer subscription model** itself — making it fundamentally harder for Google to patch without breaking Family Sharing.

### The Concept

A **Google AI subscription (Pro/Ultra)** is shareable with up to 5 family members via Google Family Sharing. Each member gets their own authenticated session with full access to Gemini.

Trinity's approach:
1. Extract the **web session cookies** (`__Secure-1PSID`, etc.) from each family member's browser
2. Inject all 6 cookie sets into a **single local Antigravity IDE instance**
3. Use **Redis** to orchestrate parallel task distribution across all 6 sessions
4. Apply **Mixture of Experts (MoE) synthesis** to produce a superior answer from multiple candidates

The traffic is **indistinguishable from legitimate web usage** — each request comes from a real, authenticated Google session cookie.

### Why It's Devastating

| Aspect | Routes 1 & 2 (Cloud) | Route 3 (Hive Swarm) |
|---|---|---|
| **Attack Vector** | Cloud API misconfiguration | Consumer subscription model |
| **Cost** | GCP trial credits (finite) | One family plan (recurring) |
| **Model Access** | gemini-flash (via API) | Gemini Pro (full web model) |
| **Throughput** | API quota-limited | **×6 parallel, no API limits** |
| **Detectability** | Cloud Audit Logs | **Invisible** — legitimate web traffic |
| **To Block** | Patch API config | **Kill Family Sharing or ban cookies in IDEs** |

### Key Features
- **Fan-Out Architecture** — Same task dispatched to ALL workers simultaneously
- **Fan-In Collection** — Waits for all responses with configurable timeout
- **MoE Synthesis** — Leader account judges and merges N candidate responses into one superior answer
- **Legitimate Network Signature** — All traffic originates from real authenticated sessions
- **Dynamic Pool** — Automatically detects available cookies (1 to 6 slots)
- **Dual Strategy** — MoE (parallel + synthesis) or Single (round-robin) modes

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    MISSION CONTROL                          │
│              (FastAPI + Redis Orchestrator)                  │
│                                                             │
│  POST /launch                                               │
│       │                                                     │
│       ▼                                                     │
│  ┌──────────────────────────────────────────┐               │
│  │           FAN-OUT DISPATCHER             │               │
│  │  Duplicates task to N worker queues      │               │
│  └──┬───┬───┬───┬───┬──────────────────────┘               │
│     │   │   │   │   │                                       │
│  ┌──▼┐┌─▼─┐┌▼──┐┌▼──┐┌─▼─┐                                │
│  │W2 ││W3 ││W4 ││W5 ││W6 │  ← Each worker has a unique    │
│  │🍪2││🍪3││🍪4││🍪5││🍪6│    Family Sharing cookie        │
│  └──┬┘└─┬─┘└┬──┘└┬──┘└─┬─┘                                │
│     │   │   │    │     │                                    │
│  ┌──▼───▼───▼────▼─────▼─────────────────┐                 │
│  │         FAN-IN COLLECTOR              │                 │
│  │  Waits for N responses in Redis       │                 │
│  └──────────┬────────────────────────────┘                 │
│             │                                               │
│  ┌──────────▼────────────────────────────┐                 │
│  │       MoE SYNTHESIZER (Leader 🍪1)    │                 │
│  │  Judges all responses, returns best   │                 │
│  └───────────────────────────────────────┘                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                    output/mission_*.md
```

### Data Flow

```text
1. User → POST /launch {"instruction": "...", "strategy": "moe"}
2. API → Redis: Push same task to hive_tasks:2, hive_tasks:3, ..., hive_tasks:6
3. Workers → Each pops from its queue, calls Gemini via its cookie
4. Workers → Redis: Push results to hive_results:{mission_id}
5. Mission Control → Collects all results (Fan-In)
6. Synthesizer → Uses Leader cookie (🍪1) to judge & merge responses
7. Output → Final answer saved to output/ directory
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Redis

**Option A — Local binary:**
Download [Redis for Windows](https://github.com/microsoftarchive/redis/releases) and place in `redis/` directory.

**Option B — Docker:**
```bash
docker run -d -p 6379:6379 redis
```

### 3. Configure cookies

```bash
cp .env.example .env
```

Open `.env` and fill in cookies for each account. To extract cookies:
1. Open `gemini.google.com` in your browser (logged in as each family member)
2. DevTools → Application → Cookies → `gemini.google.com`
3. Copy `__Secure-1PSID`, `__Secure-1PSIDTS`, `__Secure-1PSIDCC`
4. Paste into the corresponding `HIVE_{N}_*` slots in `.env`

**Minimum:** Slot 1 (leader) + Slot 2 (one worker)  
**Maximum:** Slots 1-6 (1 leader + 5 workers)

### 4. Launch a mission

```bash
python core/mission.py "Explain the architecture of a distributed cache"
```

Or with a JSON template:
```bash
python core/mission.py missions/mission_template_v2.json
```

### 5. Result

The script:
1. Starts Redis + API + N Workers (one per cookie)
2. Fans out the task to all workers simultaneously
3. Collects all independent responses
4. Synthesizes the best answer via MoE
5. Saves everything to `output/`

## File Structure

```
/
├── LICENSE                            # MIT License
├── DISCLAIMER.md                      # Educational PoC disclaimer
├── README.md                          # This file
├── .env.example                       # Cookie pool template (6 slots)
├── requirements.txt                   # Python dependencies
├── core/
│   ├── cookie_pool.py                 # Cookie pool manager (loads N cookies)
│   ├── mission.py                     # Fan-Out / Fan-In / MoE orchestrator
│   ├── worker.py                      # Per-cookie Gemini worker
│   ├── synthesizer.py                 # MoE Judge (merges N responses)
│   └── toolkit.py                     # Filesystem tools (read, write, list, exec)
├── api/
│   └── main.py                        # FastAPI gateway (launch, status, health)
└── missions/
    └── mission_template_v2.json       # Task template with strategy field
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | System status |
| `POST` | `/launch` | Launch a new mission (MoE or single) |
| `GET` | `/status/{mission_id}` | Mission progress and status |
| `GET` | `/results/{mission_id}` | All individual worker responses |
| `GET` | `/swarm/health` | Worker status and queue depths |
| `GET` | `/swarm/pool` | Cookie pool metadata (no secrets) |
| `GET` | `/queue/stats` | Redis queue statistics |

## Security

- `.env` is gitignored — cookies are never committed
- Workers use **secondary account** cookies only
- The Leader cookie is used exclusively for synthesis
- Redis runs locally — no external exposure
- No cookies are exposed via API endpoints

---
*Trinity Hackathon 2026 — Technical Demonstration*
