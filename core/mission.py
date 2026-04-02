import sys
import os
import time
import json
import subprocess
import requests

API_URL = "http://localhost:8000"
REDIS_PATH = os.path.join("redis", "redis-server.exe")

def check_hive_health():
    """Checks if the API is responsive."""
    try:
        r = requests.get(f"{API_URL}/")
        if r.status_code == 200:
            return True
    except requests.exceptions.ConnectionError:
        return False
    return False

def start_hive_infrastructure():
    """Launches Redis, API, and Workers in new windows (Minimized & Tracked)."""
    print("\U0001f41d [HIVE] Initializing V2 Distributed Swarm...")

    si = subprocess.STARTUPINFO()

    # 1. Start Redis
    if os.path.exists(REDIS_PATH):
        print("    \U0001f538 Starting Redis (Minimized/Shell)...")
        subprocess.Popen(f'start /min "AG-Redis" "{REDIS_PATH}"', shell=True)
        time.sleep(3)
    else:
        print(f"\u274c [ERROR] Redis not found at {REDIS_PATH}")
        sys.exit(1)

    # 2. Start API
    print("    \U0001f538 Starting FastAPI Gateway (Minimized)...")
    p = subprocess.Popen([sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"], startupinfo=si)
    HIVE_PROCESSES.append(p)
    time.sleep(1.2)

    # 3. Start Workers (4 Nodes)
    print("    \U0001f538 Mobilizing Worker Swarm (Minimized & Staggered)...")
    for i in range(1, 5):
        p = subprocess.Popen([sys.executable, "core/worker_v2.py"], startupinfo=si)
        HIVE_PROCESSES.append(p)
        time.sleep(1.2)

    print("    \u23f3 Waiting for Swarm Convergence...")
    for _ in range(20):
        if check_hive_health():
            print("    \u2705 Hive Infrastructure ONLINE.")
            return True
        time.sleep(0.5)

    print("\u274c [ERROR] Hive failed to stabilize.")
    return False

# Track processes for cleanup
HIVE_PROCESSES = []

def cleanup_hive():
    """Kills all spawned processes."""
    if not HIVE_PROCESSES:
        return
    print("\n\U0001f9f9 [HIVE] Shutting down Swarm (Graceful Exit)...")
    for p in HIVE_PROCESSES:
        try:
            p.terminate()
        except Exception:
            pass

def main():
    if len(sys.argv) < 2:
        print("Usage: python core/mission.py [json_file] OR 'instruction'")
        sys.exit(1)

    try:
        input_data = sys.argv[1]
        task_payload = {}

        if input_data.endswith('.json') and os.path.exists(input_data):
            with open(input_data, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "goal" in data:
                    task_payload["instruction"] = data["goal"]
                elif "instruction" in data:
                    task_payload = data
                else:
                    task_payload["instruction"] = str(data)
        else:
            task_payload["instruction"] = input_data

        print(f"\U0001f680 [MISSION] Launching: {task_payload['instruction'][:50]}...")

        if not check_hive_health():
            if not start_hive_infrastructure():
                sys.exit(1)

        try:
            r = requests.post(f"{API_URL}/launch", json=task_payload)
            r.raise_for_status()
            res = r.json()
            task_id = res['task_id']
            print(f"    \U0001f4e1 Task Injected. ID: {task_id}")
        except Exception as e:
            print(f"\u274c [API ERROR] Could not submit task: {e}")
            sys.exit(1)

        print(f"    \u23f3 Monitoring Task {task_id} (Blocking Mode)...")

        start_time = time.time()
        while True:
            try:
                status_res = requests.get(f"{API_URL}/status/{task_id}")
                if status_res.status_code == 200:
                    state = status_res.json()
                    status = state.get("status", "UNKNOWN")

                    if status == "DONE":
                        print(f"\n\u2705 [SWARM COMPLETE] Task {task_id} Finished.")
                        print("-" * 40)
                        print(state.get("result", "No result data"))
                        print("-" * 40)
                        break
                    elif status == "ERROR":
                        print(f"\n\u274c [MISSION FAILED] Task {task_id} Error.")
                        print(state.get("error", "Unknown error"))
                        break
                    else:
                        sys.stdout.write(".")
                        sys.stdout.flush()
                        time.sleep(1)
                else:
                    print("?")
                    time.sleep(1)

                if time.time() - start_time > 600:
                    print("\n\u23f0 [TIMEOUT] Mission timed out.")
                    break

            except KeyboardInterrupt:
                print("\n\U0001f6d1 [ABORT] Interrupted by user.")
                break
            except Exception as e:
                print(f"\n\u26a0\ufe0f [POLL ERROR] {e}")
                time.sleep(1)

    finally:
        cleanup_hive()

if __name__ == "__main__":
    main()
