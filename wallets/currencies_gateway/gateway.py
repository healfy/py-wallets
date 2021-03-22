import typing
from wallets.gateway.base import BaseAsyncGateway
from wallets.rpc import currencies_pb2
from wallets.rpc import currencies_grpc
from wallets.settings.config import conf
from .serializers import CurrencyRateSchema
from .exceptions import CurrenciesBadResponseException


class CurrenciesServiceGateway(BaseAsyncGateway):
    """Hold logic for interacting with remote currencies service."""

    NAME = 'currencies'
    MODULE = currencies_pb2
    response_attr = 'header'
    TIMEOUT = conf['CURRENCIES_GW_TIMEOUT']
    GW_ADDRESS = conf['CURRENCY_GRPC_ADDRESS']
    EXC_CLASS = CurrenciesBadResponseException
    ALLOWED_STATUTES = (currencies_pb2.SUCCESS,)
    BAD_RESPONSE_MSG = 'Bad response from currencies.'
    ServiceStub = currencies_grpc.CurrenciesServiceStub

    async def get_currencies(self) -> typing.Dict:
        message = self.MODULE.CurrenciesRequest()
        response = await self._base_request(message, self.CLIENT.Get)

        return CurrencyRateSchema(many=True).load(
            response.get('currencies', [])
        )
