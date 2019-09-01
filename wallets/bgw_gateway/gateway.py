import typing
from decimal import Decimal
import grpc
from google.protobuf.json_format import MessageToDict
from retrying import retry

from wallets.rpc import blockchain_gateway_pb2_grpc, bc_gw
from wallets import app
from wallets import logger
from . import serializers
from .exceptions import *


class BlockChainServiceGateWay:
    """Hold logic for interacting with remote blockchain gateway service."""

    def get_balance_by_slug(self, slug: int) -> Decimal:
        """ Get actual balance by wallet slug """
        request_message = bc_gw.GetBalanceBySlugRequest(slug=slug)

        with grpc.insecure_channel(
                app.config['BLOCKCHAIN_GW_ADDRESS']) as channel:

            client = blockchain_gateway_pb2_grpc.BlockchainGatewayServiceStub(
                channel)

            response_data = self._base_request(
                request_message,
                client.GetBalanceBySlug,
                bad_response_msg=f"Could not get balance "
                                 f"for wallet with slug={slug}."
            )

        return serializers.GetBalanceResponseSchema().load(
            response_data).get('balance')

    def get_platform_wallets_balance(self) -> typing.List:
        """ Get balance of all platform wallets """
        request_message = bc_gw.EmptyRequest()

        with grpc.insecure_channel(
                app.config['BLOCKCHAIN_GW_ADDRESS']) as channel:

            client = blockchain_gateway_pb2_grpc.BlockchainGatewayServiceStub(
                channel)

            response_data = self._base_request(
                request_message,
                client.GetPlatformWalletsBalance,
                bad_response_msg=f"Could not get balance for platform wallets."
            )

        response_data = response_data['wallets']
        return [serializers.WalletSchema().load(elem) for elem
                in response_data]

    @retry(stop_max_attempt_number=app.config['REMOTE_OPERATION_ATTEMPT_NUMBER'])
    def _base_request(self, request_message, request_method,
                      bad_response_msg: str = "Bad response from blockchain gateway.",
                      allowed_statuses: typing.Tuple[int] = (bc_gw.SUCCESS,)) -> \
            typing.Optional[typing.Dict[str, typing.Any]]:
        """
        :param request_message: protobuf message request object
        :param request_method: client request method
        :param bad_response_msg: exception message for failed status
        :param allowed_statuses: tuple of allowed response statuses,
        in actual status not in allowed_statuses it raises.
        """
        try:
            response = request_method(request_message, timeout=app.config[
                'BLOCKCHAIN_GW_TIMEOUT'])
            status = response.status.status
            if status in allowed_statuses:
                if status != bc_gw.SUCCESS:
                    logger.warning(str(
                        f"{self.__class__.__name__} got "
                        f"{bc_gw.ResponseStatus.Name(status)} "
                        f"response for request {request_message}.").replace(
                        "\n", " "))
                return MessageToDict(response, preserving_proto_field_name=True)
            raise BlockchainBadResponseException(str(
                bad_response_msg + f" Got status "
                                   f"{bc_gw.ResponseStatus.Name(status)}: "
                                   f"{response.status.description}.").replace(
                "\n", " "))
        except Exception as exc:
            logger.warning(
                f"{self.__class__.__name__} request "
                f"{request_message.__class__.__name__} got exception "
                f"{exc.__class__}: {exc}")
            raise exc
