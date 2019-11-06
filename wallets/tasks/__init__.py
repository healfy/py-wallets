import typing
import asyncio
from wallets import db
from wallets import logger
from wallets.monitoring.common import __TRANSACTIONS_TASKS__
from wallets.monitoring.common import BaseMonitorClass


@asyncio.coroutine
def run_monitoring(
        task_class: typing.Type['BaseMonitorClass']
) -> typing.NoReturn:
    """
    Generating coroutines for tasks that will be running concurrently in
    async event loop
    """

    if issubclass(task_class, BaseMonitorClass):
        while True:
            yield from asyncio.sleep(task_class.timeout)
            try:
                yield from task_class.process(db.session)
                logger.info(f'{task_class.__name__} finished')
            except Exception as e:
                logger.error(e)


__tasks__ = [
    asyncio.ensure_future(
        run_monitoring(task)) for task in __TRANSACTIONS_TASKS__
]
