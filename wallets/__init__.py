import peewee
import peewee_async

import sys
import os
from aiohttp import web_app
sys.path.extend(['/', '/app', 'wallets', 'wallets/rpc', '/app/rpc', '..', '../rpc', '/etc/wallets'])  # for docker

from wallets.settings.config import conf
from wallets.shared.logging import logger
from wallets.gateway import start_remote_gateways


class MyManager(peewee_async.Manager):

    async def get_all(self, source_, *args, **kwargs):

        await self.connect()

        if isinstance(source_, peewee.Query):
            query = source_
            model = query.model
        else:
            query = source_.select()
            model = source_

        conditions = list(args) + [(getattr(model, k) == v)
                                   for k, v in kwargs.items()]

        if conditions:
            query = query.where(*conditions)

        result = await self.execute(query)

        return list(result)

    async def exists(self, source_, *args, **kwargs):
        return bool(await self.get_all(source_, *args, **kwargs))


app = web_app.Application()
app.config = conf


database: peewee_async.PostgresqlDatabase = peewee_async.PostgresqlDatabase(
    os.getenv('PGDATABASE', 'wallets'),
    host=os.getenv('PGHOST', 'localhost'),
    user=os.getenv('PGUSER', 'postgres'),
    password=os.getenv('PGPASSWORD')
)

objects = MyManager(database)
start_remote_gateways()
