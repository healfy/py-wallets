from requests import Response
from decimal import Decimal
from unittest.mock import patch
from unittest.mock import MagicMock
from tests import BaseDB
from wallets.rpc import wallets_pb2
from wallets.gateway import method_classes
from wallets.common import Wallet
from wallets.common import Transaction
from wallets.utils.consts import TransferStatus
resp = Response()
resp.status_code = 200


class TestWalletServer(BaseDB):

    def test_healhtz_method(self):
        request = MagicMock()
        response = method_classes.HeathzMethod.process(request, self.session)
        expected_res = wallets_pb2.HealthzResponse()
        expected_res.header.status = wallets_pb2.SUCCESS
        assert response == expected_res

    @patch('requests.post', return_value=resp)
    @patch.object(method_classes.CheckBalanceMethod, 'get_html', return_value='')
    def test_check_balance_method(self, *args, **kwargs):
        request = wallets_pb2.CheckBalanceRequest(
            body_currency='bitcoin', body_amount='1'
        )
        # not sending email case
        with patch.object(method_classes.CheckBalanceMethod,
                          'get_balance',
                          return_value=Decimal('2')) as get_balance_mock:
            resp = method_classes.CheckBalanceMethod.process(request,
                                                             self.session)
            expected_res = wallets_pb2.CheckBalanceResponse()
            expected_res.header.status = wallets_pb2.SUCCESS
            assert resp == expected_res

        # sending email case
        with patch.object(method_classes.CheckBalanceMethod,
                          'get_balance',
                          return_value=Decimal('0.22')) as get_balance_mock:
            resp = method_classes.CheckBalanceMethod.process(request,
                                                             self.session)
            expected_res = wallets_pb2.CheckBalanceResponse()
            expected_res.header.status = wallets_pb2.SUCCESS
            expected_res.header.description = 'success with send email'
            assert resp == expected_res

    def test_start_monitoring_method(self):
        request = wallets_pb2.MonitoringRequest(wallet=wallets_pb2.Wallet(**{
            'id': 1,
            'currency_slug': 'bitcoin',
            'address': 'simple_address',
            'is_platform': False
        }))

        response = method_classes.StartMonitoringMethod.process(request,
                                                                self.session)

        expected_res = wallets_pb2.MonitoringResponse()
        expected_res.header.status = wallets_pb2.SUCCESS
        assert response == expected_res
        wallet = self.session.query(Wallet).filter_by(external_id=1).first()
        assert wallet is not None
        assert wallet.address == 'simple_address'
        assert wallet.is_platform == False

    def test_stop_monitoring_method(self, wallet):
        on_monitoring = wallet.on_monitoring
        request = wallets_pb2.MonitoringRequest(wallet=wallets_pb2.Wallet(**{
            'id': wallet.external_id,
            'currency_slug': wallet.currency_slug,
            'address': wallet.address,
            'is_platform': wallet.is_platform
        }))
        response = method_classes.StopMonitoringMethod.process(request,
                                                               self.session)

        expected_res = wallets_pb2.MonitoringResponse()
        expected_res.header.status = wallets_pb2.SUCCESS
        assert response == expected_res
        wallet = self.session.query(Wallet).filter_by(id=wallet.id).first()

        assert wallet.on_monitoring == False
        assert on_monitoring != wallet.on_monitoring

    def test_update_trx_method(self, transaction):
        request = wallets_pb2.TransactionRequest()
        message = transaction.to_message()
        message.transfer_status = TransferStatus.CONFIRMED.value
        request.transaction.append(message)

        response = method_classes.UpdateTrxMethod.process(request,
                                                          self.session)

        expected_res = wallets_pb2.TransactionResponse()
        expected_res.header.status = wallets_pb2.SUCCESS
        trx = self.session.query(Transaction).filter_by(hash=transaction.hash).first()
        assert response == expected_res
        assert trx.transfer_status == TransferStatus.CONFIRMED.value
        assert trx.confirmed_at is not None

    def test_get_input_trx_method(self, transactions, wallet):
        request = wallets_pb2.InputTransactionsRequest(
            wallet_id=wallet.id,
            wallet_address=wallet.address
        )
        response = method_classes.GetInputTrxMethod.process(request,
                                                            self.session)

        assert wallets_pb2.SUCCESS == response.header.status
        assert len(transactions) == len(response.transactions)
        hashes = [t.hash for t in transactions]
        assert hashes == [t.hash for t in response.transactions]
