import typing
import traceback
import asyncio
from wallets import logger
from wallets.monitoring.common import __TRANSACTIONS_TASKS__
from wallets.monitoring.common import BaseMonitorClass


async def run_monitoring(
        task_class: typing.Type['BaseMonitorClass']
) -> typing.NoReturn:
    """
    Generating coroutines for tasks that will be running concurrently in
    async event loop
    """

    if issubclass(task_class, BaseMonitorClass):
        while True:
            await asyncio.sleep(task_class.timeout)
            try:
                logger.info(f"{task_class.__name__} task started.")
                await task_class.process()
                logger.info(f'{task_class.__name__} finished')
            except Exception as e:
                logger.error(
                    f"Class {task_class.__name__} failed with "
                    f"{e.__class__.__name__}: "
                    f"{e}. {traceback.format_stack()}")


__tasks__ = [
    asyncio.ensure_future(
        run_monitoring(task)) for task in __TRANSACTIONS_TASKS__
]
