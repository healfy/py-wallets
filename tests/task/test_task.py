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
                          side_effect=[resp1, resp2]) as base_mock:
            common.CheckTransactionsMonitor.process()
        trx1 = Transaction.query.filter_by(address_from=w1.address).first()
        assert trx1 is not None
