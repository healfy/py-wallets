import io
import traceback
from abc import ABC
from decimal import Decimal
from flask import render_template

from wallets.rpc.observer_pb2_grpc import observer__pb2

from wallets import app
from wallets import logger
from wallets import request_objects
from wallets.utils import send_message
from wallets.gateway import blockchain_service_gw


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
    def process(cls, request):
        """The main method, which is called to process the request by the server.
        Must return an object of the message class that is defined individually
        for each method using
        response_msg_cls attribute.
        """
        response = cls._get_response_msg(request)
        try:
            logger.info(f"{cls.__name__}.process got request message {request}.")
            request_obj = cls.request_obj_cls.from_message(request)
            if not request_obj:
                logger.warning(f"Got invalid request data for {cls.__name__}. "
                               f"Errors: {request_obj.error}.")
                response.status.status = observer__pb2.INVALID_REQUEST
                response.status.description = request_obj.error
            else:
                response = cls._execute(request_obj, response)
        except Exception as exc:
            output = io.StringIO()
            traceback.print_tb(exc.__traceback__, None, output)
            tb = output.getvalue()
            output.close()
            logger.error(f"{cls.__name__} failed. "
                         f"Error: {exc.__class__.__name__}: {exc}. {tb}. "
                         f"Request: {request_obj}")
            response.status.status = observer__pb2.ERROR
            response.status.description = str(exc)
        return response

    @classmethod
    def _get_response_msg(cls, request):
        return cls.response_msg_cls()

    @classmethod
    def _execute(cls, request_obj, response_msg):
        """Contains the individual logic for processing a request specific to
        the server method.
        Must return a message class object (response_msg_cls instance) with a
        filled status.
        :param request_obj - request_obj_cls instance with request data.
        :param response_msg - response_msg_cls instance.
        :return response_msg_cls instance.
        """
        raise NotImplementedError


class CheckBalanceMethod(ServerMethod):

    request_obj_cls = request_objects.BalanceRequestObject
    response_msg_cls = observer__pb2.CheckBalanceResponse

    @classmethod
    def _execute(cls, request_obj, response_msg):
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
        response_msg.status.status = observer__pb2.SUCCESS
        return response_msg
