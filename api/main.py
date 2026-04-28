"""
Antigravity Hive API — FastAPI Gateway for Swarm Orchestration.

Provides HTTP endpoints to launch missions, monitor status,
and inspect the swarm health.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import uuid
import json
import time
import os
import sys

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cookie_pool import CookiePool

app = FastAPI(
    title="Antigravity Hive API",
    description="Swarm Orchestration Gateway for Trinity Hive Swarm",
    version="2.0.0",
)

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
pool = CookiePool()


class TaskRequest(BaseModel):
    instruction: str
    context: str = ""
    strategy: str = "moe"  # "moe" (fan-out + synthesis) or "single" (one worker)


@app.get("/")
def read_root():
    return {
        "system": "Antigravity Hive Swarm",
        "version": "2.0.0",
        "status": "ONLINE",
        "architecture": "Fan-Out / Fan-In / MoE Synthesis",
    }


@app.post("/launch")
def launch_mission(task: TaskRequest):
    """
    Launch a new mission into the HIVE.

    In MoE mode (default): the task is fanned-out to ALL available workers.
    Each worker generates an independent response using its own cookie/session.
    The leader then synthesizes the best answer.

    In single mode: the task goes to one worker (round-robin).
    """
    mission_id = str(uuid.uuid4())[:8]
    worker_ids = pool.worker_ids()

    if not worker_ids:
        raise HTTPException(
            status_code=503,
            detail="No worker cookies loaded. Check .env configuration.",
        )

    task_payload = {
        "mission_id": mission_id,
        "instruction": task.instruction,
        "context": task.context,
    }
    task_json = json.dumps(task_payload)

    if task.strategy == "moe":
        # FAN-OUT: push to ALL worker queues
        for wid in worker_ids:
            r.rpush(f"hive_tasks:{wid}", task_json)

        r.hset(f"mission:{mission_id}", mapping={
            "status": "COLLECTING",
            "instruction": task.instruction,
            "strategy": "moe",
            "expected": str(len(worker_ids)),
            "received": "0",
            "created_at": str(time.time()),
        })

        return {
            "mission_id": mission_id,
            "status": "COLLECTING",
            "strategy": "moe",
            "workers_dispatched": len(worker_ids),
            "worker_slots": worker_ids,
        }
    else:
        # SINGLE: push to one worker (round-robin via Redis counter)
        counter = r.incr("hive_rr_counter")
        target = worker_ids[counter % len(worker_ids)]
        r.rpush(f"hive_tasks:{target}", task_json)

        r.hset(f"mission:{mission_id}", mapping={
            "status": "PROCESSING",
            "instruction": task.instruction,
            "strategy": "single",
            "expected": "1",
            "received": "0",
            "worker": str(target),
            "created_at": str(time.time()),
        })

        return {
            "mission_id": mission_id,
            "status": "PROCESSING",
            "strategy": "single",
            "worker": target,
        }


@app.get("/status/{mission_id}")
def get_mission_status(mission_id: str):
    """Get the current status of a mission."""
    key = f"mission:{mission_id}"
    if not r.exists(key):
        raise HTTPException(status_code=404, detail="Mission not found")

    mission_data = r.hgetall(key)

    # Check for incoming results
    result_key = f"hive_results:{mission_id}"
    received = r.llen(result_key)
    mission_data["received"] = str(received)

    # Update status based on progress
    expected = int(mission_data.get("expected", "0"))
    status = mission_data.get("status", "UNKNOWN")

    if status == "COLLECTING" and received >= expected:
        mission_data["status"] = "READY_FOR_SYNTHESIS"
    elif status == "COLLECTING" and received > 0:
        mission_data["status"] = "COLLECTING"

    return mission_data


@app.get("/results/{mission_id}")
def get_mission_results(mission_id: str):
    """Get all individual worker responses for a mission."""
    result_key = f"hive_results:{mission_id}"
    raw_results = r.lrange(result_key, 0, -1)
    if not raw_results:
        raise HTTPException(status_code=404, detail="No results found")
    return {
        "mission_id": mission_id,
        "count": len(raw_results),
        "responses": [json.loads(rr) for rr in raw_results],
    }


@app.get("/swarm/health")
def get_swarm_health():
    """Returns the health status of the swarm."""
    worker_ids = pool.worker_ids()
    leader = pool.get_leader()

    worker_status = {}
    for wid in worker_ids:
        queue_name = f"hive_tasks:{wid}"
        pending = r.llen(queue_name)
        worker_status[f"worker_{wid}"] = {
            "queue": queue_name,
            "pending_tasks": pending,
            "cookie_loaded": True,
        }

    return {
        "status": "ONLINE",
        "leader": {
            "slot": 1,
            "loaded": leader is not None,
            "role": "MoE Synthesizer",
        },
        "workers": worker_status,
        "total_slots": pool.total_count(),
    }


@app.get("/swarm/pool")
def get_pool_info():
    """Returns cookie pool metadata (no secrets exposed)."""
    return {
        "total_cookies": pool.total_count(),
        "leader_loaded": pool.get_leader() is not None,
        "worker_count": pool.worker_count(),
        "worker_slots": pool.worker_ids(),
        "max_slots": 6,
    }


@app.get("/queue/stats")
def get_queue_stats():
    """Returns Redis queue statistics."""
    worker_ids = pool.worker_ids()
    stats = {}
    total_pending = 0
    for wid in worker_ids:
        pending = r.llen(f"hive_tasks:{wid}")
        stats[f"worker_{wid}"] = pending
        total_pending += pending
    return {
        "total_pending": total_pending,
        "per_worker": stats,
    }
