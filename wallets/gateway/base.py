import typing
import logging
from abc import ABC
from retrying import retry
from grpclib.client import Channel
from google.protobuf.json_format import MessageToDict
from wallets import logger
from wallets.settings.config import conf


class ResponseHandler:
    response_attr: str
    BAD_RESPONSE_MSG: str
    ALLOWED_STATUTES: typing.Tuple[int]
    NAME: str
    MODULE: typing.Any
    LOGGER: logging.Logger
    EXC_CLASS: typing.Callable
    response_attr: str

    def handle_response(self, response, request_message):
        resp_header = getattr(response, self.response_attr)
        status = resp_header.status
        if status in self.ALLOWED_STATUTES:
            if status != self.MODULE.SUCCESS:
                self.LOGGER.warning(
                    f"{self.NAME} error",
                    {
                        'status': self.MODULE.ResponseStatus.Name(status),
                        'request': request_message,
                        'from': self.__class__.__name__,
                    }
                )
            return MessageToDict(response, preserving_proto_field_name=True)
        raise self.EXC_CLASS(str(
            self.BAD_RESPONSE_MSG + f" Got status "
                                    f"{self.MODULE.ResponseStatus.Name(status)}: "
                                    f"{resp_header.description}.").replace(
            "\n", " "))


class BaseGateway(ABC, ResponseHandler):
    """
    Base class for all remote gateways that are connected with this service
    """

    GW_ADDRESS: str
    TIMEOUT: int
    BAD_RESPONSE_MSG: str
    ALLOWED_STATUTES: typing.Tuple[int]
    NAME: str
    MODULE: typing.Any
    ServiceStub: object
    LOGGER: logging.Logger = logger
    EXC_CLASS: typing.Callable
    response_attr: str = 'status'

    @retry(stop_max_attempt_number=conf['REMOTE_OPERATION_ATTEMPT_NUMBER'])
    def _base_request(self, request_message, request_method,
                      bad_response_msg: str = "",
                      extend_statutes: typing.Optional = None) -> \
            typing.Optional[typing.Dict[str, typing.Any]]:
        """
        :param request_message: protobuf message request object
        :param request_method: client request method
        """
        if bad_response_msg:
            self.BAD_RESPONSE_MSG = bad_response_msg

        if extend_statutes:
            self.ALLOWED_STATUTES += extend_statutes
        try:
            response = request_method(request_message, timeout=self.TIMEOUT)
            return self.handle_response(response, request_message)
        except Exception as exc:
            self.LOGGER.error(f"{self.NAME} error",
                           {
                               "from": self.__class__.__name__,
                               "exc": exc,
                               "exc_class": exc.__class__,
                               "request": request_message.__class__.__name__,
                           })
            raise exc


class BaseAsyncGateway(ABC, ResponseHandler):
    GW_ADDRESS: str
    GW_PORT: int = 50051
    TIMEOUT: int
    CLIENT: typing.Optional
    BAD_RESPONSE_MSG: str
    ALLOWED_STATUTES: typing.Tuple[int]
    NAME: str
    MODULE: typing.Any
    ServiceStub: typing.Any
    LOGGER: logging.Logger
    EXC_CLASS: typing.Callable
    response_attr: str

    def __init__(self):
        self.CLIENT = self.ServiceStub(Channel(self.GW_ADDRESS, self.GW_PORT))

    @retry(stop_max_attempt_number=conf['REMOTE_OPERATION_ATTEMPT_NUMBER'])
    async def _base_request(
            self,
            request_message,
            request_method,
            bad_response_msg: str = "",
            extend_statutes: typing.Optional[tuple] = None
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:

        if bad_response_msg:
            self.BAD_RESPONSE_MSG = bad_response_msg

        if extend_statutes:
            self.ALLOWED_STATUTES += extend_statutes

        try:

            async with request_method.open(timeout=self.TIMEOUT) as stream:
                await stream.send_message(request_message)
                response = await stream.recv_message()
                request_method.channel.close()
            return self.handle_response(response, request_message)

        except Exception as exc:
            logger.warning(f"{self.NAME} error",
                           {
                               "from": self.__class__.__name__,
                               "exc": exc,
                               "exc_class": exc.__class__,
                               "request": request_message.__class__.__name__,
                           })
            raise exc
