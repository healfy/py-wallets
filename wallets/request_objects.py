import abc
import typing
from google.protobuf.json_format import MessageToDict
from wallets.rpc import wallets_pb2 as w_p2


class BaseRequestObject:

    _errors: set

    def __init__(self, *args, **kwargs):
        self._errors = set()
        for k, v in kwargs.items():
            self.__dict__[k] = v

    def is_valid(self):
        self._errors.add(NotImplementedError)
        return False

    @classmethod
    def from_message(cls, msg):
        data: dict = MessageToDict(msg, preserving_proto_field_name=True)
        res = cls.from_dict(data)
        return res

    @classmethod
    def from_dict(cls, d: dict):
        res = cls(**d)
        res._dict = d
        return res

    def __bool__(self):
        return self.is_valid()

    @property
    def error(self):
        return next(iter(self._errors))  # get without removing

    def __str__(self):
        return f'<{self.__class__.__name__}: {self.__dict__}>'

    def dict(self) -> typing.Optional[dict]:
        if hasattr(self, '_dict'):
            return self._dict
        return None


class HealthzRequest(BaseRequestObject):

    def is_valid(self):
        return True


class BalanceRequestObject(BaseRequestObject):
    body_amount: str
    body_currency: str

    def is_valid(self):
        if self.body_currency and self.body_amount:
            return True
        self._errors.add(ValueError(
            'body_amount and body_currency should be provided')
        )
        return False


class WalletMessage(BaseRequestObject):
    id: int
    currency_slug: str
    address: str
    is_platform: bool

    def is_valid(self):
        if not any([self.id, self.address, self.currency_slug]):
            self._errors.add(ValueError(
                'id, address, currency_slug should be provided')
            )
            return False
        return True


class BaseMonitoringRequest(BaseRequestObject,
                            metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def dict(self) -> dict:
        """
        Description
        ===========
        Returns request data as dict. Fields are:
        * external_id
        * currency_slug
        * address
        * is_platform
        """


class MonitoringRequestObject(BaseMonitoringRequest):
    wallet: WalletMessage

    def dict(self):
        return {
            'external_id': self.wallet.id,
            'is_platform': self.wallet.is_platform,
            'address': self.wallet.address,
            'currency_slug': self.wallet.currency_slug,
        }

    def __init__(self, wallet: typing.Union[WalletMessage, w_p2.Wallet]):
        self._errors = set()
        if isinstance(wallet, w_p2.Wallet):
            self.wallet = w_p2.Wallet.from_message(wallet)
        elif isinstance(wallet, WalletMessage):
            self.wallet = wallet
        else:
            self.wallet = None

    def is_valid(self) -> bool:
        wlt = getattr(self, 'wallet', None)
        if wlt:
            if wlt.is_valid():
                return True
            else:
                self._errors.add(wlt.error)
                return False
        self._errors.add(ValueError('need wallet message to send'))
        return False


class WalletBalanceRequestObject(BaseRequestObject):

    address: str
    external_id: int

    def is_valid(self):
        if not self.address or self.external_id:
            self._errors.add(ValueError(
                'address or external_id should be provided')
            )
            return False
        return True


class TransactionRequestObject(BaseRequestObject):
    pass

