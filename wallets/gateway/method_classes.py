import io
import typing
import pytz
import traceback
from abc import ABC
from datetime import datetime, timedelta
from decimal import Decimal
from flask import render_template
from sqlalchemy import and_
from sqlalchemy.orm import Session, Query

from wallets import app
from wallets import logger
from wallets import request_objects
from wallets.utils.consts import TransactionStatus
from wallets.utils import send_message
from wallets.utils import get_exchanger_wallet
from wallets.common import Wallet
from wallets.common import Transaction
from wallets.gateway import blockchain_service_gw
from wallets.rpc import wallets_pb2 as w_pb2


class ServerMethod(ABC):
    """Base class for abstracting server-side logic.
    The main method is "process", it must be called to process the request.
    To describe the new server method, you need to create a sub class and
    implement method "_execute" in it,
    which contains the logic for processing the request.

    Attributes:
    request_obj_cls: request object class(BaseRequestObject sub class ) for
    this server method.
    response_msg_cls: class of the message that this server method
    should return.
    """
    request_obj_cls = None
    response_msg_cls = None

    @classmethod
    def process(cls, request, session: Session):
        """
        The main method, which is called to process the request by the server.
        Must return an object of the message class that is defined individually
        for each method using
        response_msg_cls attribute.
        """
        response = cls._get_response_msg()
        request_obj = None
        try:
            logger.debug(
                f"{cls.__name__}.process got request message {request}.")
            request_obj = cls.request_obj_cls.from_message(request)
            if not request_obj:
                logger.error(
                    f"Got invalid request data for {cls.__name__}. "
                    f"Errors: {request_obj.error}.",
                    {'req': request_obj.dict()})
                response.header.status = w_pb2.INVALID_REQUEST
                response.header.description = request_obj.error
            else:
                response = cls._execute(request_obj, response, session)
        except Exception as exc:
            output = io.StringIO()
            traceback.print_tb(exc.__traceback__, None, output)
            tb = output.getvalue()
            output.close()
            logger.error(f"{cls.__name__} failed. "
                         f"Error: {exc.__class__.__name__}: {exc}. {tb}",
                         {'req': request_obj.dict()})
            response.header.status = w_pb2.ERROR
            response.header.description = str(exc)
            session.rollback()
        finally:
            session.close()
        return response

    @classmethod
    def _get_response_msg(cls):
        return cls.response_msg_cls()

    @classmethod
    def _execute(cls, request_obj, response_msg, session):
        """Contains the individual logic for processing a request specific to
        the server method.
        Must return a message class object (response_msg_cls instance) with a
        filled status.
        :param request_obj - request_obj_cls instance with request data.
        :param response_msg - response_msg_cls instance.
        :return response_msg_cls instance.
        """
        raise NotImplementedError


class SaveWallet:

    @classmethod
    def _save(
            cls,
            request: typing.Union[
                request_objects.MonitoringRequestObject,
                request_objects.PlatformWLTMonitoringRequestObject
            ],
            session: Session
    ):
        data = request.dict()
        if Wallet.query.filter_by(external_id=data['external_id']).first():
            raise ValueError(f'Wallet with params: '
                             f'currency:{data["currency_slug"]} '
                             f'id:{data["external_id"]} '
                             f'address: {data["address"]} '
                             f'is already exists')
        wallet = Wallet(**data)
        try:
            session.add(wallet)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


class HeathzMethod(ServerMethod):
    request_obj_cls = request_objects.HealthzRequest
    response_msg_cls = w_pb2.HealthzResponse

    @classmethod
    def _execute(
            cls,
            request_obj: request_objects.HealthzRequest,
            response_msg: w_pb2.HealthzResponse,
            session: Session
    ) -> w_pb2.HealthzResponse:
        response_msg.header.status = w_pb2.SUCCESS
        return response_msg


class CheckBalanceMethod(ServerMethod):
    request_obj_cls = request_objects.BalanceRequestObject
    response_msg_cls = w_pb2.CheckBalanceResponse

    @classmethod
    def _execute(
            cls,
            request_obj: request_objects.BalanceRequestObject,
            response_msg: w_pb2.CheckBalanceResponse,
            session: Session
    ) -> w_pb2.CheckBalanceResponse:

        balance = cls.get_balance(request_obj.body_currency)
        if balance < Decimal(request_obj.body_amount):
            ctx = dict(
                currency=request_obj.body_currency,
                body=request_obj.body_amount,
                balance=balance,
            )
            html = cls.get_html(ctx)
            try:
                send_message(html, 'Warning')
                desc = 'success with send email'
            except Exception as exc:
                logger.error(f"{cls.__name__} failed. "
                             f"Error: {exc.__class__.__name__}: {exc}.",
                             'cant send email')
                desc = 'cant send email'
            response_msg.header.description = desc

        response_msg.header.status = w_pb2.SUCCESS
        return response_msg

    @classmethod
    def get_balance(cls, slug):
        return blockchain_service_gw.get_balance_by_slug(slug)

    @classmethod
    def get_html(cls, context):
        return render_template(app.config['ALARM_TEMPLATE'], **context)


class StartMonitoringMethod(ServerMethod,
                            SaveWallet):
    request_obj_cls = request_objects.MonitoringRequestObject
    response_msg_cls = w_pb2.MonitoringResponse

    @classmethod
    def _execute(
            cls,
            request_obj: request_objects.MonitoringRequestObject,
            response_msg: w_pb2.MonitoringResponse,
            session: Session
    ) -> w_pb2.MonitoringResponse:
        cls._save(request_obj, session)
        response_msg.header.status = w_pb2.SUCCESS
        return response_msg


class StopMonitoringMethod(ServerMethod):
    request_obj_cls = request_objects.MonitoringRequestObject
    response_msg_cls = w_pb2.MonitoringResponse

    @classmethod
    def _execute(
            cls,
            request_obj: request_objects.MonitoringRequestObject,
            response_msg: w_pb2.MonitoringResponse,
            session: Session
    ) -> w_pb2.MonitoringResponse:
        session.query(Wallet).filter(
            Wallet.external_id == request_obj.wallet.id
        ).update({'on_monitoring': False})
        session.commit()
        response_msg.header.status = w_pb2.SUCCESS
        return response_msg


class UpdateTrxMethod(ServerMethod):
    request_obj_cls = request_objects.TransactionRequestObject
    response_msg_cls = w_pb2.TransactionResponse

    @classmethod
    def _execute(
            cls,
            request_obj: request_objects.TransactionRequestObject,
            response_msg: w_pb2.TransactionResponse,
            session: Session
    ) -> w_pb2.TransactionResponse:
        counter = 0
        for trx in request_obj.transactions:
            counter += session.query(Transaction).filter(
                Transaction.hash == trx.hash).filter(
                Transaction.status.in_(Transaction.ACTIVE_STATUTES)
            ).update({
                'status': TransactionStatus.CONFIRMED.value,
                'confirmed_at': datetime.now(),
                'value': Decimal(trx.value)
            })
            session.commit()
        response_msg.header.status = w_pb2.SUCCESS
        response_msg.header.description = f'Confirmed {counter} Transactions'
        return response_msg


class GetInputTrxMethod(ServerMethod):
    request_obj_cls = request_objects.GetInputTrxRequestObject
    response_msg_cls = w_pb2.InputTransactionsResponse

    @classmethod
    def _execute(
            cls,
            request_obj: request_objects.GetInputTrxRequestObject,
            response_msg: w_pb2.InputTransactionsResponse,
            session: Session
    ) -> w_pb2.InputTransactionsResponse:

        query = Transaction.query.filter_by(
            wallet_id=request_obj.wallet_id,
            status=TransactionStatus.CONFIRMED.value
        )
        query = cls.additional_filter(request_obj, query)

        for trx in query:
            response_msg.transactions.append(
                w_pb2.Transaction(
                    hash=trx.hash,
                    wallet_id=trx.wallet_id,
                    value=str(trx.value),
                    time_confirmed=int(trx.confirmed_at.timestamp())
                )
            )
        response_msg.header.status = w_pb2.SUCCESS
        return response_msg

    @classmethod
    def additional_filter(
            cls,
            request_obj: request_objects.GetInputTrxRequestObject,
            query: Query
    ) -> typing.Iterable[Transaction]:
        date_to = datetime.utcnow().replace(hour=0, minute=0, tzinfo=pytz.utc)
        date_from = date_to - timedelta(days=1)

        if getattr(request_obj, 'time_from', None):
            date_from = datetime.fromtimestamp(request_obj.time_from).replace(
                tzinfo=pytz.utc)
        if getattr(request_obj, 'time_to', None):
            date_to = datetime.fromtimestamp(request_obj.time_to).replace(
                tzinfo=pytz.utc)
        return query.filter(
            and_(
                Transaction.created_at >= date_from,
                Transaction.created_at <= date_to
            )
        )


class StartMonitoringPlatformWLTMethod(ServerMethod):
    request_obj_cls = request_objects.PlatformWLTMonitoringRequestObject
    response_msg_cls = w_pb2.PlatformWLTMonitoringResponse

    @classmethod
    def _execute(
            cls,
            request_obj: request_objects.PlatformWLTMonitoringRequestObject,
            response_msg: w_pb2.PlatformWLTMonitoringResponse,
            session: Session
    ) -> w_pb2.PlatformWLTMonitoringResponse:
        wallet = get_exchanger_wallet(
            request_obj.wallet_address, request_obj.expected_currency)

        trx = Transaction(
            address_to=wallet.address,
            currency_slug=request_obj.expected_currency,
            address_from=request_obj.expected_address,
            value=request_obj.expected_amount,
            wallet_id=wallet.id,
            uuid=request_obj.uuid
        )
        session.add(trx)
        session.commit()
        response_msg.header.status = w_pb2.SUCCESS
        return response_msg


class AddInputTransactionMethod(ServerMethod):
    request_obj_cls = request_objects.AddInputTrxRequestObject
    response_msg_cls = w_pb2.InputTransactionResponse

    @classmethod
    def _execute(
            cls,
            request_obj: request_objects.AddInputTrxRequestObject,
            response_msg: w_pb2.PlatformWLTMonitoringResponse,
            session: Session
    ) -> w_pb2.PlatformWLTMonitoringResponse:
        wallet = get_exchanger_wallet(
            request_obj.wallet_address, request_obj.currency)

        cls.find_in_base(request_obj)

        trx = Transaction(
            address_to=wallet.address,
            currency_slug=request_obj.currency,
            address_from=request_obj.from_address,
            value=request_obj.value,
            wallet_id=wallet.id,
            uuid=request_obj.uuid,
            hash=request_obj.hash
        )
        session.add(trx)
        session.commit()
        response_msg.header.status = w_pb2.SUCCESS
        response_msg.header.description = f'added Input transaction ' \
                                          f'hash: {trx.hash}'
        return response_msg

    @staticmethod
    def find_in_base(
            request_obj: request_objects.AddInputTrxRequestObject,
    ) -> typing.NoReturn:
        if Transaction.query.filter_by(hash=request_obj.hash).first():
            raise ValueError(
                f'Get Transaction error: transaction '
                f'with hash {request_obj.hash} is already in base'
            )
