"""
Hive Worker — Cookie-Bound Gemini Agent.

Each worker process is bound to a specific cookie slot (1-6).
It listens on its dedicated Redis queue (hive_tasks:{slot_id}),
executes tasks via the Gemini web API using its unique session cookie,
and publishes results to the mission's result collection.

Usage:
    python core/worker.py <slot_id>
    python core/worker.py 2      # Start worker bound to cookie slot #2
"""

import redis
import json
import time
import os
import sys
import re

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cookie_pool import CookiePool
from core.toolkit import Toolkit
from gemini import Gemini


r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

REG_TOOL = re.compile(r"\[\[TOOL:(.*?)\|(.*?)(?:\|(.*?))?\]\]", re.DOTALL)


def create_gemini_client(cookies):
    """Create a Gemini client from a cookie dict."""
    try:
        return Gemini(cookies=cookies)
    except Exception as e:
        print(f"\u274c [AUTH ERROR] Failed to create Gemini client: {e}")
        return None


def execute_tools(response_text, toolkit):
    """Parse and execute inline tool calls from the Gemini response."""
    execution_logs = ""
    matches = REG_TOOL.findall(response_text)
    for tool_name, arg1, arg2 in matches:
        print(f"    \U0001f6e0\ufe0f  [TOOL] Executing {tool_name}...")
        result = "Error: Tool not found"
        if tool_name == "read_file":
            result = toolkit.read_file(arg1)
        elif tool_name == "write_file":
            result = toolkit.write_file(arg1, arg2)
        elif tool_name == "list_dir":
            result = toolkit.list_dir(arg1)
        elif tool_name == "run_command":
            result = toolkit.run_command(arg1)
        execution_logs += (
            f"\n> TOOL: {tool_name}({arg1})\n> RESULT: {result[:500]}...\n"
        )
    return execution_logs


def execute_task(client, task, slot_id):
    """
    Execute a single task using the Gemini client bound to this worker's cookie.

    Returns:
        dict with worker_id, response text, duration
    """
    instruction = task["instruction"]
    context = task.get("context", "")
    toolkit = Toolkit()
    project_map = toolkit.project_tree()

    full_prompt = f"""CONTEXT: {context}
PROJECT MAP:
{project_map}
----------------
TASK: {instruction}
----------------
CAPABILITIES:
You have REAL access to the file system.
To use tools, format your response like this:
[[TOOL:read_file|path/to/file]]
[[TOOL:write_file|path/to/file|content]]
[[TOOL:list_dir|path]]
[[TOOL:run_command|command]]

Step 1: Explore if needed.
Step 2: Act (Write code etc).
"""

    start = time.time()
    try:
        response = client.generate_content(full_prompt)
        text_content = response.text
        tool_results = execute_tools(text_content, toolkit)
        final_output = text_content
        if tool_results:
            final_output += "\n\n--- TOOL LOGS ---\n" + tool_results
    except Exception as e:
        final_output = f"ERROR: {e}"
        print(f"\u274c [WORKER {slot_id}] Brain failure: {e}")

    duration = round(time.time() - start, 2)

    return {
        "worker_id": slot_id,
        "response": final_output,
        "duration_s": duration,
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) < 2:
        print("Usage: python core/worker.py <slot_id>")
        print("  slot_id: Cookie slot number (1-6)")
        sys.exit(1)

    slot_id = int(sys.argv[1])

    # Load this worker's specific cookie
    pool = CookiePool()
    cookies = pool.get_slot(slot_id)
    if not cookies:
        print(
            f"\u274c [WORKER {slot_id}] No valid cookies found for slot {slot_id}. "
            f"Check .env file."
        )
        sys.exit(1)

    client = create_gemini_client(cookies)
    if not client:
        sys.exit(1)

    queue_name = f"hive_tasks:{slot_id}"
    print(
        f"\U0001f41d [HIVE WORKER {slot_id}] Online | "
        f"Queue: {queue_name} | "
        f"Cookie: ...{cookies['__Secure-1PSID'][-8:]}"
    )

    try:
        while True:
            # Block until a task arrives on this worker's dedicated queue
            _, data = r.brpop(queue_name)
            task = json.loads(data)
            mission_id = task["mission_id"]

            print(
                f"\U0001f916 [WORKER {slot_id}] Received mission {mission_id}: "
                f"{task['instruction'][:50]}..."
            )

            result = execute_task(client, task, slot_id)

            # Publish result to the mission's result collection
            result_key = f"hive_results:{mission_id}"
            r.rpush(result_key, json.dumps(result))
            r.expire(result_key, 3600)  # TTL: 1 hour

            # Save individual worker output
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(
                output_dir, f"worker_{slot_id}_mission_{mission_id}.md"
            )
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result["response"])

            print(
                f"\u2705 [WORKER {slot_id}] Mission {mission_id} complete "
                f"({result['duration_s']}s)"
            )

    except KeyboardInterrupt:
        print(f"\n\U0001f44b [WORKER {slot_id}] Shutting down.")


if __name__ == "__main__":
    main()
