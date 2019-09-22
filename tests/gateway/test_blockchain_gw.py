from unittest.mock import patch
from wallets import bgw_gateway


class TestBlockchainServiceGateway:

    def setup(self):
        self.gateway = bgw_gateway.BlockChainServiceGateWay()

    def test_get_balance_by_slug(self,
                                 get_balance_by_slug_request,
                                 get_balance_by_slug_response,
                                 get_balance_response_object):
        with patch.object(self.gateway,
                          '_base_request',
                          return_value=get_balance_by_slug_response) as base_request_mock:
            result = self.gateway.get_balance_by_slug(
                get_balance_by_slug_request)
            base_request_mock.assert_called_once()
            assert result == get_balance_response_object

    def test_get_platform_balances(self,
                                   platform_balances_response,
                                   platform_balances_response_object):
        with patch.object(self.gateway,
                          '_base_request',
                          return_value=platform_balances_response) as base_request_mock:
            result = self.gateway.get_platform_wallets_balance()
            base_request_mock.assert_called_once()
            for index, trx in enumerate(platform_balances_response_object):
                assert trx == result[index]

    def test_get_transactions_list(self,
                                   get_transactions_request,
                                   get_transactions_list_response_data,
                                   get_transactions_list_response_list
                                   ):
        with patch.object(self.gateway,
                          '_base_request',
                          return_value=get_transactions_list_response_data) as base_request_mock:
            result = self.gateway.get_transactions_list(
                **get_transactions_request)
            base_request_mock.assert_called_once()
            for index, trx in enumerate(get_transactions_list_response_list):
                assert trx == result[index]

