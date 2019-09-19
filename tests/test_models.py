import uuid
from tests import BaseDB
from wallets.common import Wallet


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


