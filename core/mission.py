"""
Mission Control — Fan-Out / Fan-In Orchestrator with MoE Synthesis.

This is the brain of the Hive Swarm. When a mission is launched:

1. FAN-OUT: The same task is pushed to ALL worker queues simultaneously.
   Each worker (bound to its own cookie/session) generates an independent response.

2. FAN-IN: Mission Control waits for all workers to complete (or timeout).
   Results are collected from Redis.

3. SYNTHESIS: The MoE Synthesizer (using the Leader's cookie) evaluates
   all candidate responses and produces the definitive, best answer.

Usage:
    python core/mission.py "Your task here"
    python core/mission.py missions/mission_template_v2.json
"""

import sys
import os
import time
import json
import subprocess
import uuid

import redis
import requests

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cookie_pool import CookiePool
from core.synthesizer import Synthesizer

API_URL = "http://localhost:8000"
REDIS_PATH = os.path.join("redis", "redis-server.exe")
MISSION_TIMEOUT = 300  # 5 minutes max per mission
HIVE_PROCESSES = []

r_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


def check_hive_health():
    """Checks if the API is responsive."""
    try:
        resp = requests.get(f"{API_URL}/", timeout=2)
        return resp.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def start_redis():
    """Start Redis server."""
    if os.path.exists(REDIS_PATH):
        print("    \U0001f538 Starting Redis (Minimized)...")
        subprocess.Popen(
            f'start /min "AG-Redis" "{REDIS_PATH}"', shell=True
        )
        time.sleep(3)
        return True
    else:
        # Try system Redis
        try:
            subprocess.Popen(
                ["redis-server", "--daemonize", "yes"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(2)
            return True
        except FileNotFoundError:
            print(f"\u274c [ERROR] Redis not found at {REDIS_PATH} or in PATH")
            return False


def start_api():
    """Start FastAPI gateway."""
    print("    \U0001f538 Starting FastAPI Gateway...")
    si = subprocess.STARTUPINFO()
    p = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
        ],
        startupinfo=si,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    HIVE_PROCESSES.append(p)
    time.sleep(1.5)


def start_workers(pool):
    """Start one worker process per loaded cookie slot (excluding leader)."""
    worker_ids = pool.worker_ids()
    print(f"    \U0001f538 Mobilizing {len(worker_ids)} Workers (staggered)...")
    si = subprocess.STARTUPINFO()
    for wid in worker_ids:
        p = subprocess.Popen(
            [sys.executable, "core/worker.py", str(wid)],
            startupinfo=si,
        )
        HIVE_PROCESSES.append(p)
        time.sleep(0.8)
    return worker_ids


def start_hive_infrastructure(pool):
    """Launches Redis, API, and Workers."""
    print("\n\U0001f41d [HIVE] Initializing Distributed Swarm...")

    if not start_redis():
        return False

    start_api()

    worker_ids = start_workers(pool)
    if not worker_ids:
        print("\u274c [ERROR] No worker cookies available. Check .env")
        return False

    print("    \u23f3 Waiting for Swarm Convergence...")
    for _ in range(20):
        if check_hive_health():
            print("    \u2705 Hive Infrastructure ONLINE.")
            print(
                f"    \U0001f41d Swarm: 1 Leader + {len(worker_ids)} Workers "
                f"(slots {worker_ids})"
            )
            return True
        time.sleep(0.5)

    print("\u274c [ERROR] Hive failed to stabilize.")
    return False


def fan_out(mission_id, task_payload, worker_ids):
    """
    FAN-OUT: Push the same task to ALL worker queues simultaneously.
    Each worker will generate an independent response.
    """
    print(f"\n\U0001f4e1 [FAN-OUT] Distributing mission {mission_id} to {len(worker_ids)} workers...")

    task_with_mission = {
        **task_payload,
        "mission_id": mission_id,
    }
    task_json = json.dumps(task_with_mission)

    for wid in worker_ids:
        queue_name = f"hive_tasks:{wid}"
        r_client.rpush(queue_name, task_json)
        print(f"    \u2192 Pushed to Worker {wid} ({queue_name})")

    # Track expected responses
    r_client.hset(f"mission:{mission_id}", mapping={
        "status": "COLLECTING",
        "instruction": task_payload["instruction"],
        "expected": str(len(worker_ids)),
        "received": "0",
        "created_at": str(time.time()),
    })


def fan_in(mission_id, expected_count, timeout=MISSION_TIMEOUT):
    """
    FAN-IN: Wait for all workers to publish their results.
    Returns list of candidate responses.
    """
    result_key = f"hive_results:{mission_id}"
    print(f"\n\u23f3 [FAN-IN] Waiting for {expected_count} responses (timeout: {timeout}s)...")

    start = time.time()
    candidates = []

    while len(candidates) < expected_count:
        elapsed = time.time() - start
        if elapsed > timeout:
            print(
                f"\n\u23f0 [TIMEOUT] Got {len(candidates)}/{expected_count} "
                f"responses in {timeout}s. Proceeding with partial results."
            )
            break

        # Check for new results
        current_count = r_client.llen(result_key)
        if current_count > len(candidates):
            # Fetch all results
            raw_results = r_client.lrange(result_key, 0, -1)
            candidates = [json.loads(r) for r in raw_results]
            r_client.hset(f"mission:{mission_id}", "received", str(len(candidates)))
            print(
                f"    \U0001f4e5 Received {len(candidates)}/{expected_count} responses"
            )
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(1)

    return candidates


def cleanup_hive():
    """Kills all spawned processes."""
    if not HIVE_PROCESSES:
        return
    print("\n\U0001f9f9 [HIVE] Shutting down Swarm...")
    for p in HIVE_PROCESSES:
        try:
            p.terminate()
        except Exception:
            pass


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) < 2:
        print("Usage: python core/mission.py <instruction|json_file>")
        print("  instruction: Direct text task")
        print("  json_file:   Path to a JSON mission file")
        sys.exit(1)

    # Parse input
    input_data = sys.argv[1]
    task_payload = {}

    if input_data.endswith(".json") and os.path.exists(input_data):
        with open(input_data, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "goal" in data:
                task_payload["instruction"] = data["goal"]
            elif "instruction" in data:
                task_payload = data
            else:
                task_payload["instruction"] = str(data)
    else:
        task_payload["instruction"] = input_data

    mission_id = str(uuid.uuid4())[:8]

    print("=" * 60)
    print(f"\U0001f680 [MISSION] {task_payload['instruction'][:60]}...")
    print(f"    ID: {mission_id}")
    print("=" * 60)

    # Load cookie pool
    pool = CookiePool()
    print(f"\n{pool.summary()}")

    if pool.worker_count() == 0:
        print("\u274c No worker cookies available. Need at least slots 2+ in .env")
        sys.exit(1)

    if not pool.get_leader():
        print("\u274c Leader cookie (slot 1) is required for MoE synthesis.")
        sys.exit(1)

    try:
        # Start infrastructure if needed
        if not check_hive_health():
            if not start_hive_infrastructure(pool):
                sys.exit(1)

        worker_ids = pool.worker_ids()

        # === PHASE 1: FAN-OUT ===
        fan_out(mission_id, task_payload, worker_ids)

        # === PHASE 2: FAN-IN ===
        candidates = fan_in(mission_id, len(worker_ids))

        if not candidates:
            print("\u274c [MISSION FAILED] No responses received.")
            r_client.hset(f"mission:{mission_id}", "status", "ERROR")
            sys.exit(1)

        # === PHASE 3: MOE SYNTHESIS ===
        print(f"\n\U0001f9e0 [SYNTHESIS] MoE Judge analyzing {len(candidates)} candidates...")
        r_client.hset(f"mission:{mission_id}", "status", "SYNTHESIZING")

        synthesizer = Synthesizer(pool.get_leader())

        # Log candidate quality before synthesis
        rankings = synthesizer.judge_quality(candidates)
        for rank in rankings:
            print(
                f"    Worker {rank['worker_id']}: "
                f"{rank['response_length']} chars, "
                f"{rank['duration_s']}s"
            )

        final_answer = synthesizer.synthesize(
            task_payload["instruction"], candidates
        )

        # === PHASE 4: OUTPUT ===
        r_client.hset(f"mission:{mission_id}", mapping={
            "status": "DONE",
            "result": final_answer[:10000],  # Redis value size limit
        })

        # Save to file
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"mission_{mission_id}_final.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Mission {mission_id}\n\n")
            f.write(f"**Task:** {task_payload['instruction']}\n\n")
            f.write(f"**Workers:** {len(candidates)}\n\n")
            f.write("---\n\n")
            f.write("## Synthesized Answer (MoE)\n\n")
            f.write(final_answer)
            f.write("\n\n---\n\n## Individual Responses\n\n")
            for c in candidates:
                f.write(f"### Worker {c['worker_id']} ({c['duration_s']}s)\n\n")
                f.write(c["response"])
                f.write("\n\n")

        print("\n" + "=" * 60)
        print(f"\u2705 [MISSION COMPLETE] {mission_id}")
        print(f"    Workers: {len(candidates)} responded")
        print(f"    Output:  {output_file}")
        print("=" * 60)
        print("\n" + final_answer[:500])
        if len(final_answer) > 500:
            print(f"\n    ... ({len(final_answer)} chars total — see {output_file})")

    finally:
        cleanup_hive()


if __name__ == "__main__":
    main()
