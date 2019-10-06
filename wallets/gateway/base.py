import typing
import logging
from abc import ABC
from retrying import retry
from google.protobuf.json_format import MessageToDict
from wallets import logger
from wallets.settings.config import conf


class BaseGateway(ABC):
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
    LOGGER: logging.Logger
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
            self.bad_response_msg = bad_response_msg

        if extend_statutes:
            self.ALLOWED_STATUTES += extend_statutes
        try:
            response = request_method(request_message, timeout=self.TIMEOUT)
            header = getattr(response, self.response_attr)
            status = header.status
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
                self.bad_response_msg + f" Got status "
                                        f"{self.MODULE.ResponseStatus.Name(status)}: "
                                        f"{response.status.description}.").replace("\n", " "))
        except Exception as exc:
            logger.warning(f"{self.NAME} error",
                           {
                               "from": self.__class__.__name__,
                               "exc": exc,
                               "exc_class": exc.__class__,
                               "request": request_message.__class__.__name__,
                           })
            raise exc
