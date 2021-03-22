import uuid
from tests import BaseTestCase
from wallets.common import Wallet
from wallets.common import Transaction


class TestWalletModel(BaseTestCase):

    async def test_wallet_init(self):
        wallet = await self.manager.create(
            Wallet,
            currency_slug='bitcoin',
            address=uuid.uuid4(),
            external_id=223
        )

        self.assertEqual(wallet.currency_slug, 'bitcoin')
        self.assertEqual(wallet.external_id, 223)
        self.assertFalse(wallet.is_platform)
        self.assertTrue(wallet.on_monitoring)


class TestTransactionModel(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.wallet = Wallet(
            currency_slug='bitcoin',
            address=uuid.uuid4(),
            external_id=223
        )
        self.wallet.save()

    async def test_transaction_init(self):
        hash_ = str(uuid.uuid4())
        trx = await self.manager.create(Transaction,
                                        hash=hash_,
                                        address_from=uuid.uuid4(),
                                        address_to=str(uuid.uuid4()),
                                        value='1.23',
                                        currency_slug='bitcoin',
                                        wallet=self.wallet
                                        )
        self.assertEqual(trx.hash, hash_)
        self.assertEqual(trx.currency_slug, 'bitcoin')
        self.assertIsNotNone(trx.id)
