import os
import sys
import json
import asyncio
import consul.aio
sys.path.extend(["../", "./", "../rpc", "./rpc"])

from grpclib.server import Server
from wallets import app, logger
from wallets.gateway.server import WalletsService


@asyncio.coroutine
def watch_config():
    """
    Description
    -----------
    watch for consul config update
    """
    c = consul.aio.Consul(host=os.getenv("CONSUL", "localhost"))
    index = None
    while True:
        yield from asyncio.sleep(1)
        try:
            if os.getenv("CONSUL_PATH") is None:
                continue
            index, data = yield from c.kv.get(os.getenv("CONSUL_PATH"), index=index)
            if data is not None:
                data = json.loads(data['Value'])
                app.config.update(data)
                logger.info("config updated from consul")
        except Exception:
            logger.info("consul read config error")


def serve():
    addr, port = app.config['ADDRESS'], app.config['PORT']
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(watch_config())
    server = Server([WalletsService()], loop=loop)
    loop.run_until_complete(server.start(addr, port))
    logger.info(f"starting observer server {addr}:{port}")
    print(f"starting observer server {addr}:{port}")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == '__main__':
    serve()
