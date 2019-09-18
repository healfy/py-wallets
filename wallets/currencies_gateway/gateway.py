import grpc
import typing
from google.protobuf.json_format import MessageToDict
from wallets.gateway.base import BaseGateway
from wallets.rpc import currencies_pb2
from wallets.rpc import currencies_pb2_grpc
from wallets.settings.config import conf
from .serializers import CurrencyRateSchema


class CurrenciesServiceGateway(BaseGateway):
    """Hold logic for interacting with remote currencies service."""

    GW_ADDRESS = conf['CURRENCY_GRPC_ADDRESS']
    TIMEOUT = conf['CURRENCIES_GW_TIMEOUT']
    MODULE = currencies_pb2
    ServiceStub = currencies_pb2_grpc.CurrenciesServiceStub

    def get_currencies(self) -> typing.Dict:
        with grpc.insecure_channel(self.GW_ADDRESS) as channel:
            stub = self.ServiceStub(channel)

            response = stub.Get(
                self.MODULE.CurrenciesRequest(), timeout=self.TIMEOUT)

        message = MessageToDict(response, preserving_proto_field_name=True)
        message = message['currencies']
        return CurrencyRateSchema(many=True).load(message)
