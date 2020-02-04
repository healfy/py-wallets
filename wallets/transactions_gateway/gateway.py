import grpc
import typing
from wallets.gateway.base import BaseGateway
from wallets.rpc import transactions_pb2
from wallets.rpc import transactions_pb2_grpc
from wallets.settings.config import conf
from wallets.common.models import Transaction
from .exceptions import TransactionsBadResponseException


class TransactionsServiceGateway(BaseGateway):
    """Hold logic for interacting with remote Transactions service."""

    GW_ADDRESS = conf['TRANSACTIONS_GW_ADDRESS']
    TIMEOUT = conf['TRANSACTIONS_GW_TIMEOUT']
    MODULE = transactions_pb2
    ServiceStub = transactions_pb2_grpc.TransactionsStub
    response_attr: str = 'header'
    EXC_CLASS = TransactionsBadResponseException
    NAME = 'transactions'
    ALLOWED_STATUTES = (transactions_pb2.SUCCESS,)
    BAD_RESPONSE_MSG = ''

    def put_on_monitoring(self,
                          transactions: typing.Iterable[Transaction]
                          ) -> typing.Dict:

        request_message = self.MODULE.StartMonitoringRequest()

        for trx in transactions:
            transaction = self.MODULE.Transaction(
                **{
                    'from': trx.address_from,
                    'to': trx.address_to,
                    'currencySlug': trx.currency_slug,
                    'wallet_id': trx.wallet_id,
                    'value': str(trx.value),
                    'hash': trx.hash,
                }
            )
            request_message.transactions.append(transaction)

        with grpc.insecure_channel(self.GW_ADDRESS) as channel:
            client = self.ServiceStub(channel)

            resp_data = self._base_request(
                request_message,
                client.StartMonitoring,
            )
        return resp_data
