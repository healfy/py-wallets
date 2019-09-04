import grpc
import typing
from decimal import Decimal
from google.protobuf.json_format import MessageToDict
from retrying import retry

from wallets.rpc import blockchain_gateway_pb2 as bc_gw
from wallets.rpc import blockchain_gateway_pb2_grpc as bgw_grpc
from wallets.settings.config import conf
from wallets import logger
from .exceptions import BlockchainBadResponseException
from .serializers import (
    WalletSchema,
    TransactionSchema,
    GetBalanceResponseSchema,
)


class BlockChainServiceGateWay:
    """Hold logic for interacting with remote blockchain gateway service."""

    gw_address: str = conf['BLOCKCHAIN_GW_ADDRESS']
    timeout: int = conf['BLOCKCHAIN_GW_TIMEOUT']
    bad_response_msg: str = 'Bad response from blockchain gateway.'
    allowed_statuses: typing.Tuple[int] = (bc_gw.SUCCESS,)

    def get_balance_by_slug(self, slug: str) -> Decimal:
        """ Get actual balance by wallet slug """
        request_message = bc_gw.GetBalanceBySlugRequest(slug=slug)

        with grpc.insecure_channel(self.gw_address) as channel:
            client = bgw_grpc.BlockchainGatewayServiceStub(
                channel)

            response_data = self._base_request(
                request_message,
                client.GetBalanceBySlug,
                bad_response_msg=f"Could not get balance "
                                 f"for wallet with slug={slug}."
            )

        return GetBalanceResponseSchema().load(
            response_data).get('balance')

    def get_platform_wallets_balance(self) -> typing.List:
        """ Get balance of all platform wallets """
        request_message = bc_gw.EmptyRequest()

        with grpc.insecure_channel(self.gw_address) as channel:
            client = bgw_grpc.BlockchainGatewayServiceStub(
                channel)

            response_data = self._base_request(
                request_message,
                client.GetPlatformWalletsBalance,
                bad_response_msg=f"Could not get balance for platform wallets."
            )

        return [WalletSchema().load(elem) for elem in response_data['wallets']]

    def get_transactions_list(self, external_id: int = None,
                              wallet_address: str = None) -> typing.Dict:

        """Return transactions list for wallet identifiable by id or address.
        """
        if not any([external_id, wallet_address]):
            raise ValueError(
                'Expect at least one of external_id, wallet_address'
            )

        message = bc_gw.GetTransactionsListRequest(
            walletId=external_id, walletAddress=wallet_address)

        with grpc.insecure_channel(self.gw_address) as channel:
            client = bgw_grpc.BlockchainGatewayServiceStub(channel)
            response_data = self._base_request(
                message,
                client.GetTransactionsList,
                bad_response_msg=f"Could not get transaction "
                                 f"list with params {message}."
            )
        return TransactionSchema(many=True).load(
            response_data.get('transactions', [])
        )

    @retry(
        stop_max_attempt_number=conf['REMOTE_OPERATION_ATTEMPT_NUMBER'])
    def _base_request(self, request_message, request_method,
                      bad_response_msg: str = "") -> \
            typing.Optional[typing.Dict[str, typing.Any]]:
        """
        :param request_message: protobuf message request object
        :param request_method: client request method
        :param bad_response_msg: exception message for failed method
        in actual status not in allowed_statuses it raises.
        """
        if bad_response_msg:
            self.bad_response_msg = bad_response_msg
        try:
            response = request_method(request_message, timeout=self.timeout)
            status = response.status.status
            if status in self.allowed_statuses:
                if status != bc_gw.SUCCESS:
                    logger.warning(str(
                        f"{self.__class__.__name__} got "
                        f"{bc_gw.ResponseStatus.Name(status)} "
                        f"response for request {request_message}.").replace(
                        "\n", " "))
                return MessageToDict(response, preserving_proto_field_name=True)
            raise BlockchainBadResponseException(str(
                self.bad_response_msg + f" Got status "
                                        f"{bc_gw.ResponseStatus.Name(status)}: "
                                        f"{response.status.description}.").replace(
                "\n", " "))
        except Exception as exc:
            logger.warning(
                f"{self.__class__.__name__} request "
                f"{request_message.__class__.__name__} got exception "
                f"{exc.__class__}: {exc}")
            raise exc
