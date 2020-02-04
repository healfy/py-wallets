import grpc
import typing
from decimal import Decimal

from wallets import logger
from wallets.settings.config import conf
from wallets.common import TransactionSchema
from wallets.gateway.base import BaseGateway
from wallets.rpc import blockchain_gateway_pb2
from wallets.rpc import blockchain_gateway_pb2_grpc


from .exceptions import BlockchainBadResponseException
from .serializers import (
    WalletBalanceSchema,
    GetBalanceResponseSchema,
)


class BlockChainServiceGateWay(BaseGateway):
    """Hold logic for interacting with remote blockchain gateway service."""

    GW_ADDRESS = conf['BLOCKCHAIN_GW_ADDRESS']
    TIMEOUT = conf['BLOCKCHAIN_GW_TIMEOUT']
    BAD_RESPONSE_MSG = 'Bad response from blockchain gateway.'
    ALLOWED_STATUTES = (blockchain_gateway_pb2.SUCCESS,)
    NAME = 'bgw'
    MODULE = blockchain_gateway_pb2
    ServiceStub = blockchain_gateway_pb2_grpc.BlockchainGatewayServiceStub
    LOGGER = logger
    EXC_CLASS = BlockchainBadResponseException

    def get_balance_by_slug(self, slug: str) -> Decimal:
        """ Get actual balance by wallet slug """
        request_message = self.MODULE.GetBalanceBySlugRequest(slug=slug)

        with grpc.insecure_channel(self.GW_ADDRESS) as channel:
            client = self.ServiceStub(channel)

            response_data = self._base_request(
                request_message,
                client.GetBalanceBySlug,
                bad_response_msg=f"Could not get balance "
                                 f"for wallet with slug={slug}."
            )

        return GetBalanceResponseSchema().load(response_data).get('balance')

    def get_platform_wallets_balance(self) -> typing.List:
        """ Get balance of all platform wallets """
        request_message = self.MODULE.EmptyRequest()

        with grpc.insecure_channel(self.GW_ADDRESS) as channel:
            client = self.ServiceStub(channel)

            resp_data = self._base_request(
                request_message,
                client.GetPlatformWalletsBalance,
                bad_response_msg=f"Could not get balance for platform wallets."
            )

        return [
            WalletBalanceSchema().load(elem) for elem in resp_data['wallets']
        ]

    def get_transactions_list(self, external_id: int = None,
                              wallet_address: str = None) -> typing.List:

        """Return transactions list for wallet identifiable by id or address.
        """
        if not wallet_address:
            raise ValueError(
                'Expect at least one of external_id, wallet_address'
            )

        message = self.MODULE.GetTransactionsListRequest(
            walletId=external_id, walletAddress=wallet_address)

        with grpc.insecure_channel(self.GW_ADDRESS) as channel:
            client = self.ServiceStub(channel)

            response_data = self._base_request(
                message,
                client.GetTransactionsList,
                bad_response_msg=f"Could not get transaction "
                                 f"list with params {message}."
            )
            resp_data = response_data.get('transactions', [])
        return [
            TransactionSchema().load(elem) for elem in resp_data
        ]
