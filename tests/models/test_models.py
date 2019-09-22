import uuid
from tests import BaseDB
from wallets.common import Wallet
from wallets.common import Transaction


class TestModels(BaseDB):
    def test_wallet_init(self):
        wallet = Wallet(
            currency_slug='bitcoin',
            address=uuid.uuid4(),
            external_id=223
        )
        self.session.add(wallet)
        self.session.commit()

        assert wallet.currency_slug == 'bitcoin'
        assert wallet.external_id == 223
        assert wallet.is_platform == False
        assert wallet.on_monitoring == True

    def test_transaction_init(self, wallet):
        hash_ = str(uuid.uuid4())
        trx = Transaction(
            hash=hash_,
            address_from=wallet.address,
            address_to=str(uuid.uuid4()),
            value='1.23',
            currency_slug=wallet.currency_slug,
            wallet_id=wallet.id
        )
        self.session.add(trx)
        self.session.commit()
        self.session.refresh(trx)
        assert trx.id > 0
        assert trx.hash == hash_
        assert trx.currency_slug == wallet.currency_slug
        assert trx.address_from == wallet.address
        assert trx.wallet_id == wallet.id

    def test_wallet_from_dct(self, wallet_req_object_dict):

        wallet = Wallet.from_dict(wallet_req_object_dict)
        self.session.add(wallet)
        self.session.commit()

        assert wallet.currency_slug == 'bitcoin'
        assert wallet.external_id == 1
        assert wallet.is_platform == True
        assert wallet.on_monitoring == True
