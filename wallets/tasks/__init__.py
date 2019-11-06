import asyncio
from wallets import db
from wallets import conf
from wallets import logger
from wallets.monitoring.common import __TRANSACTIONS_TASKS__
from wallets.monitoring.common import CheckWalletMonitor


@asyncio.coroutine
def check_wallets():
    while True:
        yield from asyncio.sleep(conf['MONITORING_WALLETS_PERIOD'])
        yield from CheckWalletMonitor.process(db.session)


@asyncio.coroutine
def create_async_task(func, timeout):
    while True:
        yield from asyncio.sleep(timeout)
        try:
            yield from func(db.session)
        except Exception as e:
            logger.error(e)


futures = [
    create_async_task(task.process, conf['MONITORING_TRANSACTIONS_PERIOD'])
    for task in __TRANSACTIONS_TASKS__
]
