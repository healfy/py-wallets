from requests import Response
from decimal import Decimal
from unittest.mock import patch
from unittest.mock import MagicMock
from tests import BaseDB
from wallets.rpc import wallets_pb2
from wallets.gateway import method_classes
from wallets.common import Wallet
from wallets.common import Transaction
from wallets.utils.consts import TransactionStatus
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
    @patch.object(method_classes.CheckBalanceMethod, 'get_html',
                  return_value='')
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
        message.status = TransactionStatus.CONFIRMED.value
        request.transaction.append(message)

        response = method_classes.UpdateTrxMethod.process(request,
                                                          self.session)

        expected_res = wallets_pb2.TransactionResponse()
        expected_res.header.status = wallets_pb2.SUCCESS
        expected_res.header.description = "Confirmed 1 Transactions"
        trx = self.session.query(Transaction).filter_by(
            hash=transaction.hash).first()
        assert response == expected_res
        assert trx.status == TransactionStatus.CONFIRMED.value
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

    def test_add_input_transaction_method(self, transaction_add_message):
        trx = transaction_add_message['trx']
        req = wallets_pb2.InputTransactionRequest(**trx)

        response = method_classes.AddInputTransactionMethod.process(
            req, self.session
        )
        assert wallets_pb2.SUCCESS == response.header.status
        assert f'added Input transaction hash: ' \
               f'{req.hash}' == response.header.description
        trx = self.session.query(Transaction).filter_by(hash=req.hash).first()

        assert trx
        assert trx.wallet.address == req.wallet_address

    def test_get_exchanger_wallet_error(self, transaction_add_message):
        trx = transaction_add_message['trx']
        req = wallets_pb2.InputTransactionRequest(**trx)
        req.wallet_address = 'another_wallet'

        response = method_classes.AddInputTransactionMethod.process(
            req, self.session
        )
        assert wallets_pb2.ERROR == response.header.status
        text = "Get wallet error: the wallet another_wallet " \
               "ans slug bitcoin is not found."
        assert response.header.description == text

    def test_find_in_base_error(self, transaction_add_message_new):
        trx = transaction_add_message_new['trx']
        req = wallets_pb2.InputTransactionRequest(**trx)

        response = method_classes.AddInputTransactionMethod.process(
            req, self.session
        )
        assert wallets_pb2.ERROR == response.header.status
        text = f'Get Transaction error: transaction '\
               f'with hash {req.hash} is already in base'
        assert response.header.description == text
