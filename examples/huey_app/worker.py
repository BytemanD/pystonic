from threading import Thread

import uvicorn
from fastapi import FastAPI

from examples.huey_app.tasks import HUEY
from pystonic import context
from pystonic.log import setup_logger

setup_logger(remove=True)


@HUEY.pre_execute()
def set_context(task):
    context.set_trace()


# API for health check
API = FastAPI()


@API.get("/livez")
async def livez():
    return {}


api_thread = Thread(target=uvicorn.run, args=(API,), kwargs={"port": 8001}, daemon=True)
api_thread.start()
