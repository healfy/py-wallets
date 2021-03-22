import uuid
from asyncio import Future
from decimal import Decimal
from unittest.mock import patch

from wallets import bgw_gateway
from tests import BaseTestCase


class TestBGWServiceGateway(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.gateway = bgw_gateway.BlockChainServiceGateWay()

    @staticmethod
    def wallet_msg(slug, value='1234'):
        return {'currencySlug': slug, 'value': value}

    @staticmethod
    def wallet_result_msg(slug, value='1234'):
        return {'currencySlug': slug, 'value': Decimal(value)}

    @staticmethod
    def transaction_response_data(value=1):
        return {
            'from': 'some_wallet_address',
            'to': 'some_wallet_address',
            'currencySlug': 'bitcoin',
            'value': f'{value}',
            'hash': f'{value}simple_hash'
        }

    def get_transactions_list_response_data(self):
        return {
            'transactions': [self.transaction_response_data(value=i) for i in
                             range(1, 3)]
        }

    @staticmethod
    def transaction_response_result(value=1):
        return {
            'hash': f'{value}simple_hash',
            'value': Decimal(f'{value}'),
            'address_from': 'some_wallet_address',
            'currency_slug': 'bitcoin',
            'address_to': 'some_wallet_address'
        }

    def get_transactions_list_response_list(self):
        return [
            self.transaction_response_result(i) for i in range(1, 3)
        ]

    async def test_get_balance_by_slug(self):
        result = Future()
        result.set_result({'balance': '12345'})
        with patch.object(self.gateway,
                          '_base_request',
                          return_value=result
                          ) as base_request_mock:
            result = await self.gateway.get_balance_by_slug('bitcoin')
            base_request_mock.assert_called_once()

        self.assertEqual(result, Decimal('12345'))

    async def test_get_platform_balances(self):
        slugs = ['bitcoin', 'eth', 'binance']
        resp = Future()
        resp.set_result({
            'wallets': [self.wallet_msg(slug) for slug in slugs]
        })
        res = [self.wallet_result_msg(slug) for slug in slugs]

        with patch.object(self.gateway,
                          '_base_request',
                          return_value=resp) as base_request_mock:

            result = await self.gateway.get_platform_wallets_balance()
            base_request_mock.assert_called_once()

        for index, trx in enumerate(res):
            self.assertEqual(trx, result[index])

    async def test_get_transactions_list(self):
        req = {'external_id': 233, 'wallet_address': str(uuid.uuid4())}
        resp = Future()
        resp.set_result(self.get_transactions_list_response_data())
        with patch.object(self.gateway,
                          '_base_request',
                          return_value=resp) as base_request_mock:

            result = await self.gateway.get_transactions_list(**req)
            base_request_mock.assert_called_once()

        for index, trx in enumerate(self.get_transactions_list_response_list()):
            assert trx == result[index]
