import typing
from decimal import Decimal
from datetime import datetime

from wallets.settings.config import conf
from wallets.common import TransactionSchema
from wallets.gateway.base import BaseAsyncGateway
from wallets.rpc import blockchain_gateway_pb2
from wallets.rpc import blockchain_gateway_grpc


from .exceptions import BlockchainBadResponseException
from .serializers import (
    WalletBalanceSchema,
    GetBalanceResponseSchema,
)


class BlockChainServiceGateWay(BaseAsyncGateway):
    """Hold logic for interacting with remote blockchain gateway service."""

    NAME = 'bgw'
    GW_PORT = 50052
    response_attr = 'status'
    MODULE = blockchain_gateway_pb2
    TIMEOUT = conf['BLOCKCHAIN_GW_TIMEOUT']
    GW_ADDRESS = conf['BLOCKCHAIN_GW_ADDRESS']
    EXC_CLASS = BlockchainBadResponseException
    ALLOWED_STATUTES = (blockchain_gateway_pb2.SUCCESS,)
    BAD_RESPONSE_MSG = 'Bad response from blockchain gateway.'
    ServiceStub = blockchain_gateway_grpc.BlockchainGatewayServiceStub

    async def get_balance_by_slug(self, slug: str) -> Decimal:
        """ Get actual balance by wallet slug """
        request_message = self.MODULE.GetBalanceBySlugRequest(slug=slug)

        response_data = await self._base_request(
            request_message,
            self.CLIENT.GetBalanceBySlug,
            bad_response_msg=f"Could not get balance "
                             f"for wallet with slug={slug}."
        )

        return GetBalanceResponseSchema().load(response_data).get('balance')

    async def get_platform_wallets_balance(self) -> typing.List:
        """ Get balance of all platform wallets """
        request_message = self.MODULE.EmptyRequest()

        resp_data = await self._base_request(
            request_message,
            self.CLIENT.GetPlatformWalletsBalance,
            bad_response_msg=f"Could not get balance for platform wallets."
        )

        return [
            WalletBalanceSchema().load(elem) for elem in resp_data['wallets']
        ]

    async def get_transactions_list(
            self,
            external_id: int = None,
            wallet_address: str = None
    ) -> typing.List:

        """Return transactions list for wallet identifiable by id or address.
        """
        if not wallet_address or not external_id:
            raise ValueError(
                'Expect at least one of external_id, wallet_address'
            )

        message = self.MODULE.GetTransactionsListRequest(
            walletId=external_id, walletAddress=wallet_address)

        response_data = await self._base_request(
            message,
            self.CLIENT.GetTransactionsList,
            bad_response_msg=f"Could not get transaction "
                             f"list with params {message}."
        )
        resp_data = response_data.get('transactions', [])
        return [
            TransactionSchema().load(elem) for elem in resp_data
        ]

    async def get_exchanger_wallet_trx_list(
            self,
            slug: str,
            from_time: typing.Optional[datetime] = None,
            to_time: typing.Optional[datetime] = None,
    ) -> typing.Iterable:

        from_time = int(datetime.timestamp(from_time)) if from_time else None
        to_time = int(datetime.timestamp(to_time)) if to_time else None

        message = self.MODULE.GetTrxExchangersListRequest(
            slug=slug,
            fromTime=from_time,
            toTime=to_time
        )
        response_data = await self._base_request(
            message,
            self.CLIENT.GetTrxListExchangerWallet,
            bad_response_msg=f"Could not get transaction "
                             f"list with params {message}."
        )
        resp_data = response_data.get('transactions', [])

        return [
            TransactionSchema().load(elem) for elem in resp_data
        ]
