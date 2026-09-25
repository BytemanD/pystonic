from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from pystonic.common.log import setup_logger

from . import tasks

setup_logger(remove=True)

APP = FastAPI()


@APP.get("/livez")
def livez():
    return {}


@APP.post("/api/v1/tasks/{task_name}")
async def run_task(task_name: str, body: dict):
    if not hasattr(tasks, task_name):
        raise HTTPException(status_code=400, detail=f"invalid task: {task_name}")

    tasks.sync_source.schedule(args=(body.get("source_id"),), delay=1)
    return JSONResponse(status_code=201, content={"msg": "task commited"})
