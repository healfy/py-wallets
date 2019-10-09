from tests import BaseDB
from unittest.mock import patch
from wallets.monitoring import common
from wallets.common import Transaction


class TestTask(BaseDB):

    def test_check_trx(self, check_input_trxs_objects):
        resp1 = check_input_trxs_objects['trx1_resp']
        resp2 = check_input_trxs_objects['trx2_resp']
        w1 = check_input_trxs_objects['wallet1']
        w2 = check_input_trxs_objects['wallet2']
        with patch.object(common.b_gw,
                          '_base_request',
                          side_effect=[resp1, resp1, resp1,
                                       resp1, resp1, resp1, resp2]) as base_mock:
            common.CheckTransactionsMonitor.process(self.session)
        trx1 = Transaction.query.filter_by(wallet_id=w1.id).one()
        assert trx1 is not None
        assert trx1.address_to == w1.address
        assert trx1.hash is not None
        trx2 = Transaction.query.filter_by(wallet_id=w2.id).one()
        assert trx2 is not None
        assert trx2.address_to == w2.address
        assert trx2.hash is not None
