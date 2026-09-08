from fastapi import HTTPException
from fastapi.responses import JSONResponse

from pystonic.asgi.app import create_app
from pystonic.task_scheduler.drivers.apscheduler import APSchedulerDriver

from . import tasks

driver = APSchedulerDriver()
# print(driver.get_jobs())
driver.start(paused=True)
APP = create_app()


@APP.post("/api/v1/tasks/{task_name}")
async def run_task(task_name: str, body: dict):
    if not hasattr(tasks, task_name):
        raise HTTPException(status_code=400, detail=f"invalid task: {task_name}")

    driver.run_job(getattr(tasks, task_name), kwargs=body)
    return JSONResponse(status_code=201, content={"msg": "task commited"})
