from concurrent import futures

from loguru import logger

from pystonic import context


def _do_something(x):
    context.set_trace(f"trace-{x}")
    for i in range(5):
        logger.info(f"foo {i}")


def test_logger():
    context.setvars(name="main_task")
    logger.debug("test log ...")
    logger.info("starting")
    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        for _ in executor.map(_do_something, ["task1", "task2"]):
            pass
    logger.info("done")
