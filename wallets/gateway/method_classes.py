import io
import traceback
from abc import ABC
from decimal import Decimal
from flask import render_template
from sqlalchemy.orm.scoping import scoped_session

from wallets import app
from wallets import logger
from wallets import request_objects
from wallets.utils import send_message
from wallets.common import Wallet
from wallets.gateway import blockchain_service_gw
from wallets.rpc.wallets_pb2_grpc import wallets__pb2 as w_pb2


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
    def process(cls, request, session: scoped_session):
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
                response.status.status = w_pb2.INVALID_REQUEST
                response.status.description = request_obj.error
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
            response.status.status = w_pb2.ERROR
            response.status.description = str(exc)
            session.rollback()
        finally:
            session.remove()
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


class SaveWalletMixin:

    @classmethod
    def _save(
            cls,
            request: request_objects.BaseMonitoringRequest,
            session
    ):
        if issubclass(request.__class__, request_objects.BaseMonitoringRequest):
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
            session
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
            session
    ) -> w_pb2.CheckBalanceResponse:

        balance = blockchain_service_gw.get_balance_by_slug(
            request_obj.body_currency)
        if balance < Decimal(request_obj.body_amount):
            ctx = dict(
                currency=request_obj.body_currency,
                body=request_obj.body_amount,
                balance=balance,
            )
            html = render_template(app.config['ALARM_TEMPLATE'], **ctx)
            send_message(html, 'Warning')
        response_msg.header.status = w_pb2.SUCCESS
        return response_msg


class StartMonitoringMethod(ServerMethod, SaveWalletMixin):

    request_obj_cls = request_objects.MonitoringRequestObject
    response_msg_cls = w_pb2.MonitoringResponse

    @classmethod
    def _execute(
            cls,
            request_obj: request_objects.MonitoringRequestObject,
            response_msg: w_pb2.MonitoringResponse,
            session
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
            session
    ) -> w_pb2.MonitoringResponse:

        session.query(Wallet).filter(
            Wallet.external_id == request_obj.wallet.id
        ).update({'on_monitoring': False})
        session.commit()
        response_msg.header.status = w_pb2.SUCCESS
        return response_msg
