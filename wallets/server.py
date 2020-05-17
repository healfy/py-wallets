import os
import sys
import json
import asyncio
import consul.aio
sys.path.extend(["../", "./", "../rpc", "./rpc"])

from grpclib.server import Server
from wallets import app, logger
from wallets.gateway.server import WalletsService
from wallets.tasks import run_monitoring
from wallets.monitoring.common import __TRANSACTIONS_TASKS__


async def watch_config():
    """
    Description
    -----------
    watch for consul config update
    """
    c = consul.aio.Consul(host=os.getenv("CONSUL", "localhost"))
    index = None
    while True:
        await asyncio.sleep(1)
        try:
            if os.getenv("CONSUL_PATH") is None:
                continue
            index, data = await c.kv.get(os.getenv("CONSUL_PATH"), index=index)
            if data is not None:
                data = json.loads(data['Value'])
                app.config.update(data)
                logger.info("config updated from consul")
        except Exception:
            logger.info("consul read config error")


def end_gracefully_tasks(loop):
    to_cancel = asyncio.all_tasks(loop)

    for task in to_cancel:
        task.cancel()

    loop.run_until_complete(
        asyncio.gather(*to_cancel, loop=loop, return_exceptions=True))

    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'unhandled exception during shutdown',
                'exception': task.exception(),
                'task': task,
            })


def serve():
    addr, port = app.config['ADDRESS'], app.config['PORT']
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(None)
    for t in __TRANSACTIONS_TASKS__:
        loop.create_task(run_monitoring(t))
    server = Server([WalletsService()], loop=loop)
    loop.run_until_complete(server.start(addr, port))
    logger.info(f"starting wallets server {addr}:{port}")

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('Got signal SIGINT, "shutting down"')

    end_gracefully_tasks(loop)
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == '__main__':
    serve()
