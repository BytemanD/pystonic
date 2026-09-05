import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from examples.huey_app import tasks
from pystonic.log import setup_logger

setup_logger(remove=True)

APP = FastAPI()


@APP.get("/livez")
def livez():
    return {}


worker_client = httpx.AsyncClient(base_url="http://localhost:8001")


@APP.post("/api/v1/tasks/{task_name}")
async def run_task(task_name: str, body: dict):
    if not hasattr(tasks, task_name):
        raise HTTPException(status_code=400, detail=f"invalid task: {task_name}")
    getattr(tasks, task_name)(**body)
    return JSONResponse(status_code=201, content={"msg": "task commited"})
