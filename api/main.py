from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import uuid
import json
import os

app = FastAPI(title="Antigravity Hive API")
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

class TaskRequest(BaseModel):
    instruction: str
    context: str = ""
    files: str = ""

@app.get("/")
def read_root():
    return {"system": "Antigravity Hive", "status": "ONLINE"}

@app.post("/launch")
def launch_task(task: TaskRequest):
    """Injects a new task into the HIVEMIND (Redis)."""
    task_id = str(uuid.uuid4())[:8]
    payload = {
        "id": task_id,
        "instruction": task.instruction,
        "context": task.context,
        "files": task.files,
        "status": "QUEUED"
    }
    r.rpush("antigravity_tasks", json.dumps(payload))
    r.hset(f"task:{task_id}", mapping=payload)
    return {"task_id": task_id, "status": "QUEUED"}

@app.get("/status/{task_id}")
def get_status(task_id: str):
    if not r.exists(f"task:{task_id}"):
        raise HTTPException(status_code=404, detail="Task not found")
    return r.hgetall(f"task:{task_id}")

@app.get("/queue/len")
def get_queue_length():
    return {"pending_tasks": r.llen("antigravity_tasks")}
