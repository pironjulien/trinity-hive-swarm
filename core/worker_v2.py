import redis
import json
import time
import os
import sys
import re
from toolkit import Toolkit

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

from gemini import Gemini

def get_gemini_client():
    cookies = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('GEMINI_'):
                    parts = line.strip().split('=')
                    if len(parts) >= 2:
                        raw_key = parts[0]
                        value = parts[1].strip('"').strip()
                        if raw_key == "GEMINI___Secure-1PSID":
                            cookies['__Secure-1PSID'] = value
                        elif raw_key == "GEMINI___Secure-1PSIDTS":
                            cookies['__Secure-1PSIDTS'] = value
                        elif raw_key == "GEMINI___Secure-1PSIDCC":
                            cookies['__Secure-1PSIDCC'] = value
                        elif raw_key.startswith("GEMINI_"):
                            k = raw_key.replace("GEMINI_", "")
                            cookies[k] = value
        return Gemini(cookies=cookies)
    except Exception as e:
        print(f"\u274c [AUTH ERROR] {e}")
        return None

REG_TOOL = re.compile(r"\[\[TOOL:(.*?)\|(.*?)(?:\|(.*?))?\]\]", re.DOTALL)

def execute_tools(response_text, toolkit):
    execution_logs = ""
    matches = REG_TOOL.findall(response_text)
    for tool_name, arg1, arg2 in matches:
        print(f"    \U0001f6e0\ufe0f [TOOL] Executing {tool_name}...")
        result = "Error: Tool not found"
        if tool_name == 'read_file':
            result = toolkit.read_file(arg1)
        elif tool_name == 'write_file':
            result = toolkit.write_file(arg1, arg2)
        elif tool_name == 'list_dir':
            result = toolkit.list_dir(arg1)
        elif tool_name == 'run_command':
            result = toolkit.run_command(arg1)
        execution_logs += f"\n> TOOL: {tool_name}({arg1})\n> RESULT: {result[:500]}...\n"
    return execution_logs

def execute_agent_logic(task):
    task_id = task['id']
    instruction = task['instruction']
    context = task.get('context', '')
    toolkit = Toolkit()
    project_map = toolkit.project_tree()
    print(f"\U0001f916 [V2 AGENT] Received Mission: {instruction[:50]}...")
    client = get_gemini_client()
    if not client:
        return "ERROR: No Brain Connection"

    full_prompt = f"""
    CONTEXT: {context}
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

    try:
        response = client.generate_content(full_prompt)
        text_content = response.text
        tool_results = execute_tools(text_content, toolkit)
        final_output = text_content + "\n\n--- TOOL LOGS ---\n" + tool_results
    except Exception as e:
        final_output = f"ERROR: {e}"
        print(f"\u274c [BRAIN FAIL] {e}")

    output_filename = f"output/v2_brain_{task_id}.md"
    os.makedirs('output', exist_ok=True)
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(final_output)
    return final_output

def process_task(task):
    task_id = task['id']
    r.hset(f"task:{task_id}", "status", "PROCESSING")
    try:
        result = execute_agent_logic(task)
        r.hset(f"task:{task_id}", "result", result)
        r.hset(f"task:{task_id}", "status", "DONE")
        print(f"\u2705 [WORKER] Task {task_id} COMPLETED.")
    except Exception as e:
        print(f"\u274c [WORKER] Task {task_id} FAILED: {e}")
        r.hset(f"task:{task_id}", "status", "ERROR")
        r.hset(f"task:{task_id}", "error", str(e))

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("\U0001f41d [HIVE WORKER V2.1] AGENTIC MODE (Tools Enabled)...")
    try:
        while True:
            _, data = r.brpop("antigravity_tasks")
            task = json.loads(data)
            process_task(task)
    except KeyboardInterrupt:
        print("\n\U0001f44b [WORKER] Shutting down.")

if __name__ == "__main__":
    main()
