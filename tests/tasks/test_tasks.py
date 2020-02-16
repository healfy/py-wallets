from unittest.mock import patch
from tests import BaseDB
from wallets.common import Transaction
from wallets.utils.consts import TransactionStatus
from wallets.monitoring import common


class TestTask(BaseDB):

    def test_check_input_trx(self, check_input_trxs_objects):
        resp1 = check_input_trxs_objects['trx1_resp']
        resp2 = check_input_trxs_objects['trx2_resp']
        w1 = check_input_trxs_objects['wallet1']
        w2 = check_input_trxs_objects['wallet2']
        # dirty hack for test monitoring
        # count of response object == all count of wallets in db
        with patch.object(common.b_gw,
                          '_base_request',
                          side_effect=[resp1,
                                       resp1,
                                       resp1,
                                       resp1,
                                       resp1,
                                       resp1, resp2]) as base_mock:
            common.CheckTransactionsMonitor.process(self.session)
        trx1 = Transaction.query.filter_by(wallet_id=w1.id).first()
        assert trx1 is not None
        assert trx1.address_to == w1.address
        assert trx1.hash == resp1['transactions'][0]['hash']
        trx2 = Transaction.query.filter_by(wallet_id=w2.id).first()
        assert trx2 is not None
        assert trx2.address_to == w2.address
        assert trx2.hash == resp2['transactions'][0]['hash']

    def test_check_exchanger_trx(self, check_exch_trxs_objects):
        resp1 = check_exch_trxs_objects['trx1_resp']
        resp2 = check_exch_trxs_objects['trx2_resp']
        w1 = check_exch_trxs_objects['wallet1']
        w2 = check_exch_trxs_objects['wallet2']
        # dirty hack for test monitoring
        # count of response object == all count of platform wallets in db
        with patch.object(common.b_gw,
                          '_base_request',
                          side_effect=[resp1, resp1, resp2]) as base_mock:
            common.CheckPlatformWalletsMonitor.process(self.session)
        trx1 = Transaction.query.filter_by(wallet_id=w1.id).first()
        assert trx1 is not None
        assert trx1.address_to == w1.address
        assert trx1.hash == resp1['transactions'][0]['hash']
        trx2 = Transaction.query.filter_by(wallet_id=w2.id).first()
        assert trx2 is not None
        assert trx2.address_to == w2.address
        assert trx2.hash == resp2['transactions'][0]['hash']

    def test_send_to_trx_service(self, transaction):
        with patch.object(common.transactions_service_gw,
                          '_base_request',
                          return_value={}) as base_mock:
            common.SendToTransactionService.process(self.session)

        trx = Transaction.query.filter_by(id=transaction.id).first()
        assert trx.status == TransactionStatus.SENT.value

    def test_send_to_exchanger_service(self, exchanger_transaction):
        with patch.object(common.exchanger_service_gw,
                          '_base_request',
                          return_value={}) as base_mock:
            common.SendToExchangerService.process(self.session)

        trx = Transaction.query.filter_by(id=exchanger_transaction.id).first()
        assert trx.status == TransactionStatus.REPORTED.value
