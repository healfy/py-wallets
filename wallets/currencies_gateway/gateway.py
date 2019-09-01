import grpc
import typing
from google.protobuf.json_format import MessageToDict
from wallets.rpc import currencies_pb2_grpc, currencies_pb2
from wallets import app
from .serializers import CurrencyRateSchema


class CurrenciesServiceGateway:
    """Hold logic for interacting with remote currencies service."""

    def get_currencies(self) -> typing.Dict:
        with grpc.insecure_channel(app.config['CURRENCY_GRPC_ADDRESS']) as channel:
            stub = currencies_pb2_grpc.CurrenciesServiceStub(channel)

            response = stub.Get(currencies_pb2.CurrenciesRequest(), timeout=5)
        message = MessageToDict(response, preserving_proto_field_name=True)
        message = message['currencies']
        return CurrencyRateSchema(many=True).load(message)



