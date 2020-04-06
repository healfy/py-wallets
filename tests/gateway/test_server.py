import uuid
import pytest
from requests import Response
from decimal import Decimal
from unittest.mock import patch
from unittest.mock import MagicMock
from tests import test_db
from tests import BaseTestCase
from wallets.rpc import wallets_pb2
from wallets.gateway import method_classes
from wallets.common import Wallet
from wallets.common import Transaction
from wallets.utils.consts import TransactionStatus

resp = Response()
resp.status_code = 200


@pytest.fixture(autouse=True)
def transaction():
    with test_db.transaction() as txn:
        yield txn
        txn.rollback()


@pytest.mark.usefixtures('transaction')
class TestWalletServer(BaseTestCase):

    async def test_healhtz_method(self):
        request = MagicMock()
        response = await method_classes.HeathzMethod.process(request)
        expected_res = wallets_pb2.HealthzResponse()
        expected_res.header.status = wallets_pb2.SUCCESS
        self.assertEqual(response, expected_res)

    @patch('requests.post', return_value=resp)
    @patch.object(method_classes.CheckBalanceMethod, 'get_html',
                  return_value='')
    async def test_check_balance_method(self, *args, **kwargs):
        request = wallets_pb2.CheckBalanceRequest(
            body_currency='bitcoin', body_amount='1'
        )
        # not sending email case
        with patch.object(method_classes.CheckBalanceMethod,
                          'get_balance',
                          return_value=Decimal('2')) as get_balance_mock:
            resp = await method_classes.CheckBalanceMethod.process(request)
            get_balance_mock.assert_called_once()

        expected_res = wallets_pb2.CheckBalanceResponse()
        expected_res.header.status = wallets_pb2.SUCCESS
        self.assertEqual(resp, expected_res)

        # sending email case
        with patch.object(method_classes.CheckBalanceMethod,
                          'get_balance',
                          return_value=Decimal('0.22')) as get_balance_mock:
            resp = await method_classes.CheckBalanceMethod.process(request)
            get_balance_mock.assert_called_once()

        expected_res = wallets_pb2.CheckBalanceResponse()
        expected_res.header.status = wallets_pb2.SUCCESS
        expected_res.header.description = 'success with send email'
        self.assertEqual(resp, expected_res)

    async def test_start_monitoring_method(self):
        request = wallets_pb2.MonitoringRequest(wallet=wallets_pb2.Wallet(**{
            'id': 1,
            'currency_slug': 'bitcoin',
            'address': 'simple_address',
            'is_platform': False
        }))

        response = await method_classes.StartMonitoringMethod.process(request)

        expected_res = wallets_pb2.MonitoringResponse()
        expected_res.header.status = wallets_pb2.SUCCESS
        self.assertEqual(response, expected_res)
        wallet = await self.manager.get(Wallet, external_id=1)
        self.assertIsNotNone(wallet)
        self.assertEqual(wallet.address, 'simple_address')
        self.assertFalse(wallet.is_platform)

    async def test_stop_monitoring_method(self):
        self.wallet = await self.manager.create(
            Wallet,
            currency_slug='bitcoin',
            address='23123123',
            external_id=2
        )
        on_monitoring = self.wallet.on_monitoring
        request = wallets_pb2.MonitoringRequest(wallet=wallets_pb2.Wallet(**{
            'id': self.wallet.external_id,
            'currency_slug': self.wallet.currency_slug,
            'address': self.wallet.address,
            'is_platform': self.wallet.is_platform
        }))
        response = await method_classes.StopMonitoringMethod.process(request)

        expected_res = wallets_pb2.MonitoringResponse()
        expected_res.header.status = wallets_pb2.SUCCESS
        self.assertEqual(response, expected_res)
        wallet = await self.manager.get(Wallet, id=self.wallet.id)

        self.assertFalse(wallet.on_monitoring)
        self.assertNotEqual(on_monitoring, wallet.on_monitoring)

    async def test_update_trx_method(self):
        trx = await self.manager.create(Transaction, **{
            'hash': str(uuid.uuid4()),
            'value': '123',
            'address_from': 'some_wallet_address',
            'currency_slug': 'bitcoin',
            'address_to': 'some_wallet_address',
            'uuid': str(uuid.uuid4()),
        })
        request = wallets_pb2.TransactionRequest()
        message = trx.to_message()
        message.status = TransactionStatus.CONFIRMED.value
        request.transaction.append(message)

        response = await method_classes.UpdateTrxMethod.process(request)

        expected_res = wallets_pb2.TransactionResponse()
        expected_res.header.status = wallets_pb2.SUCCESS
        expected_res.header.description = "Confirmed 1 Transactions"
        trx = await self.manager.get(Transaction, id=trx.id)
        self.assertEqual(response, expected_res)
        self.assertEqual(trx.status, TransactionStatus.CONFIRMED.value)
        self.assertIsNotNone(trx.confirmed_at)

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
        text = f'Get Transaction error: transaction ' \
               f'with hash {req.hash} is already in base'
        assert response.header.description == text
