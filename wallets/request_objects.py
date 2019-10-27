import abc
import typing
from google.protobuf.json_format import MessageToDict
from wallets.utils.consts import TransactionStatus
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
    external_id: int

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.external_id = self.id

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
        raise NotImplementedError('Base class dont have any methods')


class MonitoringRequestObject(BaseMonitoringRequest):
    wallet: typing.Union[WalletMessage, typing.Dict]

    def dict(self):
        return {
            'external_id': self.wallet.id,
            'is_platform': getattr(self.wallet, 'is_platform', False),
            'address': self.wallet.address,
            'currency_slug': self.wallet.currency_slug,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._errors = set()
        self.wallet = WalletMessage.from_dict(self.wallet)

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


class TransactionMessage(BaseRequestObject):
    fromAddr: str  # be carefull! This name is different from proto-file
    to: str
    currencySlug: str
    value: str
    hash: str
    status: int
    is_fee_trx: bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = self.get_status(self.status)

    @classmethod
    def from_dict(cls, d: dict):
        """
        we should override this method for field with name 'from'
        due to python reserved words
        """
        fromAddr = d.pop('from', None)
        if fromAddr:
            d['fromAddr'] = fromAddr
        return cls(**d)

    def is_valid(self) -> bool:
        if getattr(self, 'fromAddr', None) and \
                getattr(self, 'hash', None) and \
                getattr(self, 'to', None) and \
                getattr(self, 'value', None) and \
                getattr(self, 'currencySlug', None):
            return True
        self._errors.add(ValueError('Not enough transaction params to send!'))
        return False

    def dict(self) -> typing.Dict:
        return self.clean_dict({
            'id': getattr(self, 'id', None),
            'address_to': self.to,
            'address_from': self.fromAddr,
            'currency_slug': self.currencySlug,
            'value': self.value,
            'hash': self.hash,
            'status': self.status,
            'is_fee_trx': getattr(self, 'is_fee_trx', None),
        })

    @staticmethod
    def clean_dict(dictionary: typing.Dict) -> typing.Dict:
        return {
            key: dictionary[key] for key in dictionary if dictionary.get(key)
        }

    @staticmethod
    def get_status(value):
        _TO_TRX_STATUS_ = {
            w_p2.TransactionStatus.Name(w_p2.NEW): TransactionStatus.NEW.value,
            w_p2.TransactionStatus.Name(w_p2.CONFIRMED): TransactionStatus.CONFIRMED.value,
            w_p2.TransactionStatus.Name(w_p2.FAILED): TransactionStatus.FAILED.value,
            w_p2.TransactionStatus.Name(w_p2.PENDING): TransactionStatus.PENDING.value,
            w_p2.TransactionStatus.Name(w_p2.NOT_FOUND): TransactionStatus.NOT_FOUND.value,
            w_p2.TransactionStatus.Name(w_p2.SUCCESSFUL): TransactionStatus.SUCCESSFUL.value,
            w_p2.TransactionStatus.Name(w_p2.UNDEFINED): TransactionStatus.UNDEFINED.value,
        }
        return _TO_TRX_STATUS_[value] if value else None


class TransactionRequestObject(BaseMonitoringRequest):

    transactions: typing.List[TransactionMessage]

    def __init__(self, transaction: typing.List):
        self._errors = set()
        self.transactions = [
            TransactionMessage.from_dict(trx) for trx in transaction
        ] if transaction else None

    def is_valid(self) -> bool:
        validated = []

        if getattr(self, 'transactions'):
            for trx in self.transactions:
                if not trx.is_valid():
                    self._errors.add(trx.error)
                else:
                    validated.append(trx)
            is_valid = self.__eq__(validated)
            if not is_valid:
                return False
            return True

        self._errors.add(ValueError('Not enough transaction to update!'))
        return False

    def dict(self) -> dict:
        return {}

    def __eq__(self, other):
        return len(self.transactions) == len(other)


class GetInputTrxRequestObject(BaseRequestObject):

    wallet_id: int
    wallet_address: str
    currencySlug: str
    time_from: int
    time_to: int

    def is_valid(self):
        if not self.wallet_id:
            self._errors.add(
                ValueError('wallet_id is required'))
            return False
        return True


class PlatformWLTMonitoringRequestObject(BaseMonitoringRequest):
    wallet: typing.Union[WalletMessage, typing.Dict]
    expected_address: str
    expected_amount: str

    def dict(self):
        return {
            'external_id': self.wallet.id,
            'is_platform': getattr(self.wallet, 'is_platform', False),
            'address': self.wallet.address,
            'currency_slug': self.wallet.currency_slug,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._errors = set()
        self.wallet = WalletMessage.from_dict(self.wallet)

    def is_valid(self) -> bool:
        wlt = getattr(self, 'wallet', None)
        expected_address = getattr(self, 'expected_address', None)
        expected_amount = getattr(self, 'expected_amount', None)
        if all([wlt, expected_address, expected_amount]):
            if wlt.is_valid():
                return True
            else:
                self._errors.add(wlt.error)
                return False
        self._errors.add(ValueError('need expected_address, wallet message to '
                                    'send'))
        return False
