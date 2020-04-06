import asyncio
import aiounittest
from wallets import database
from wallets import objects
from wallets.common import Wallet
from wallets.common import Transaction

MODELS = [Wallet, Transaction]

database.database = 'test_wallets'
test_db = database


class BaseTestCase(aiounittest.AsyncTestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = test_db

        # Bind model classes to test db. Since we have a complete list of
        # all models, we do not need to recursively bind dependencies.
        cls.test_db.bind(MODELS, bind_refs=False, bind_backrefs=False)

        cls.test_db.connect()
        cls.test_db.create_tables(MODELS)
        cls.manager = objects

    @classmethod
    def tearDownClass(cls):
        cls.test_db.drop_tables(MODELS)

        # Close connection to db.
        cls.test_db.close()

    def get_event_loop(self):
        self.my_loop = asyncio.get_event_loop()
        return self.my_loop
