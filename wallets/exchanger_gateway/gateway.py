import grpc
import typing
from wallets.gateway.base import BaseGateway
from wallets.rpc import exchanger_pb2
from wallets.rpc import exchanger_pb2_grpc
from wallets.settings.config import conf
from wallets.common.models import Transaction
from .exceptions import ExchangerBadResponseException


class ExchangerServiceGateway(BaseGateway):
    """Hold logic for interacting with remote Exchanger service."""

    GW_ADDRESS = conf['EXCHANGER_GW_ADDRESS']
    TIMEOUT = conf['EXCHANGER_GW_TIMEOUT']
    MODULE = exchanger_pb2
    ServiceStub = exchanger_pb2_grpc.ExchangerServiceStub
    response_attr: str = 'header'
    EXC_CLASS = ExchangerBadResponseException
    NAME = 'exchanger'
    BAD_RESPONSE_MSG = 'Bad response from exchanger service'
    ALLOWED_STATUTES = (exchanger_pb2.SUCCESS,)

    async def update_transactions(
            self,
            transactions: typing.Iterable[Transaction]
    ) -> typing.Dict:

        request_message = self.MODULE.UpdateRequest()

        for trx in transactions:
            transaction = self.MODULE.TransactionData(
                **{
                    'uuid': trx.uuid,
                    'value': str(trx.value),
                    'trx_hash': trx.hash,
                }
            )
            request_message.transactions.append(transaction)

        with grpc.insecure_channel(self.GW_ADDRESS) as channel:
            client = self.ServiceStub(channel)

            resp_data = self._base_request(
                request_message,
                client.UpdateInputTransaction,
            )
        return resp_data
