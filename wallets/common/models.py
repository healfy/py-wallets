import pytz
import warnings
import typing
from copy import deepcopy
from datetime import datetime
from typing import TYPE_CHECKING
from google.protobuf.json_format import MessageToDict
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    DECIMAL,
    Text,
    func,
    inspect,
    ForeignKey
)
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_mixins import AllFeaturesMixin

from .seriallizers import WalletSchema
from .seriallizers import TransactionSchema
from wallets.utils.consts import TransactionStatus
from wallets.rpc import wallets_pb2

if TYPE_CHECKING:
    Base = object
else:
    Base = declarative_base()


def row2dict(obj, exclude=None) -> dict:
    fields_dict = {}
    if exclude is None:
        exclude = ()
    if obj is not None:
        fields = {c.key: getattr(obj, c.key) for c in
                  inspect(obj).mapper.column_attrs}
        for f in inspect(obj).mapper.relationships:
            if f.key != 'versions' and (
                    not f.back_populates or f.key == 'borrower'):  # TODO: fix this dirty hack
                rel = getattr(obj, f.key)
                if rel is not None:
                    fields_dict[f.key] = rel.dict()
        for key, v in fields.items():
            if not key.startswith('_') and not key.endswith(
                    '_id') and key not in exclude:
                val = getattr(obj, key)
                fields_dict[key] = val.dict(exclude=exclude) if hasattr(val, 'dict') else val
    return fields_dict


class BaseModel(Base, AllFeaturesMixin):
    schema_class = None  # marshmallow schema class
    message_class = None  # proto message for this model
    __abstract__ = True

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True)

    created_at = Column('created_at',
                        DateTime(timezone=True),
                        nullable=False,
                        default=datetime.utcnow())

    updated_at = Column('updated_at',
                        DateTime(timezone=True),
                        nullable=False,
                        default=datetime.utcnow(),
                        onupdate=datetime.utcnow())
    deleted_at = Column('deleted_at',
                        DateTime(timezone=True),
                        default=None)

    is_deleted = Column(Boolean,
                        comment='Is deleted row',
                        nullable=False,
                        default=False,
                        index=True)

    def _as_message_dict(self):
        raise NotImplementedError('NotImplemented')

    def to_message(self):
        return self.message_class(**self._as_message_dict())

    @classmethod
    def from_message(cls, msg):
        schema = cls.schema_class()
        return cls.from_dict(
            schema.load(MessageToDict(msg, preserving_proto_field_name=True)))

    def __repr__(self) -> str:
        return "<Model{} ({})>".format(self.__class__.__name__, self.id)

    def dates_dict(self) -> dict:
        warnings.warn(
            f'method dates_dict of Base for '
            f'{self.__class__.__name__} will be removed!', DeprecationWarning
        )
        return {
            'created_at': self.created_at__ts,
            'updated_at': self.updated_at__ts,
            'deleted_at': self.deleted_at__ts,
        }

    def get_created_at(self):
        return self.created_at

    def delete(self):
        self.deleted_at = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.is_deleted = True

    @classmethod
    def from_dict(cls, d: typing.Dict):
        res: dict = deepcopy(d)
        for rel in inspect(cls).relationships:
            if rel.key in res and isinstance(res[rel.key], dict):
                res[rel.key] = rel.mapper.class_.from_dict(res[rel.key])
                res[rel.key + "_id"] = res[rel.key].id
        new_obj = cls(**res)
        return new_obj

    def save(self):
        raise NotImplementedError('Mixing save cannot store versions')

    def update(self):
        raise NotImplementedError('Mixing update cannot store versions')


class Wallet(BaseModel):
    """Wallets of platform and borrowers"""

    __tablename__ = "wallets"

    schema_class = WalletSchema
    message_class = wallets_pb2.Wallet

    currency_slug = Column(Text,
                           comment='Wallet currency slug',
                           nullable=False)

    address = Column(Text,
                     comment='Wallet address',
                     nullable=False)

    external_id = Column(Integer,
                         comment='id from deposits bridge serve for joining',
                         index=True,
                         nullable=False)

    is_platform = Column(Boolean,
                         comment='is platform wallet',
                         default=False,
                         nullable=False)

    on_monitoring = Column(Boolean,
                           comment='on monitoring',
                           default=True,
                           nullable=False,
                           index=True)

    def _as_message_dict(self) -> typing.Dict:
        return {
            'id': self.id,
            'address': self.address,
            'is_platform': self.is_platform,
            'currency_slug': self.currency_slug,
            'external_id': self.external_id,
        }


class Transaction(BaseModel):
    """BlockChain transaction"""

    __tablename__ = "transactions"

    schema_class = TransactionSchema
    message_class = wallets_pb2.Transaction

    status = Column(Integer,
                    index=True,
                    default=TransactionStatus.NEW.value,
                    nullable=False,
                    comment='current transaction status')
    hash = Column(Text,
                  nullable=False,
                  comment='transaction hash',
                  unique=True)

    address_from = Column(Text,
                          comment='initiator of transaction')

    address_to = Column(Text,
                        comment='to whom transfer transaction')

    currency_slug = Column(Text,
                           comment='transaction currency')

    value = Column(DECIMAL,
                   comment='transactions amount')

    is_fee_trx = Column(Boolean,
                        comment='Is it transaction to send fee on wallet',
                        default=False)

    wallet_id = Column(Integer,
                       ForeignKey('wallets.id'),
                       nullable=True,
                       default=None,
                       index=True)

    wallet = relationship("Wallet",
                          foreign_keys='Transaction.wallet_id',
                          cascade='merge',
                          cascade_backrefs=False,
                          backref='transaction')

    confirmed_at = Column(DateTime,
                          nullable=True,
                          default=None,
                          comment='time in that transaction confirmed'
                          )

    def _as_message_dict(self) -> typing.Dict:
        return {
            'to': self.address_to,
            'from': self.address_from,
            'currencySlug': self.currency_slug,
            'value': f'{self.value}',
            'hash': self.hash,
        }

    def set_confirmed(self,
                      status: TransactionStatus,
                      session: Session
                      ) -> typing.NoReturn:

        if status == TransactionStatus.CONFIRMED.value:
            status = TransactionStatus.CONFIRMED.value
            confirmed_at = datetime.now().replace(tzinfo=pytz.utc)
            self.outer_update(session, status=status, confirmed_at=confirmed_at)

    def outer_update(self,
                     session: Session,
                     **params: typing.Optional
                     ) -> typing.NoReturn:
        session.query(Transaction).filter_by(id=self.id).update(params)
        session.commit()
