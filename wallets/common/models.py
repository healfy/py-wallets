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
    Numeric,
    Text,
    func,
    inspect,
    JSON)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_continuum import make_versioned
from sqlalchemy_mixins import AllFeaturesMixin

from .seriallizers import WalletSchema
from wallets.rpc import wallets_pb2

if TYPE_CHECKING:
    Base = object
else:
    Base = declarative_base()

make_versioned(options={'native_versioning': True}, user_cls=None)


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
                fields_dict[key] = val.dict(exclude=exclude) if hasattr(val,
                                                                        'dict') else val
    return fields_dict


class BaseModel(Base, AllFeaturesMixin):
    schema_class = None  # marshmallow schema class
    message_class = None  # proto message for this model
    __abstract__ = True

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True)

    __created_at = Column(
        'created_at',
        DateTime(timezone=True),
        nullable=False,
        default=func.now())

    __updated_at = Column('updated_at',
                          DateTime(timezone=True),
                          nullable=False,
                          default=func.now(),
                          onupdate=func.now())
    __deleted_at = Column('deleted_at',
                          DateTime(timezone=True),
                          default=None)

    is_deleted = Column(Boolean,
                        comment='Is deleted row',
                        nullable=False,
                        default=False,
                        index=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.created_at = func.now()
        self.updated_at = func.now()

    def to_message(self):
        data = self.schema_class().dump(self).data
        return self.message_class(**data)

    @classmethod
    def from_message(cls, msg):
        schema = cls.schema_class()
        return cls.from_dict(
            schema.load(MessageToDict(msg, preserving_proto_field_name=True)
                        ).data)

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
        return self.__created_at

    def delete(self):
        self.deleted_at = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.is_deleted = True

    def dict(self, exclude=None) -> typing.Dict[str, typing.Any]:
        return row2dict(self, exclude)

    @classmethod
    def from_dict(cls, d: typing.Dict):
        res: dict = deepcopy(d)
        for rel in inspect(cls).relationships:
            if rel.key in res and isinstance(res[rel.key], dict):
                res[rel.key] = rel.mapper.class_.from_dict(res[rel.key])
                res[rel.key + "_id"] = res[rel.key].id
        new_obj = cls(**res)
        return new_obj

    def update_from_dict(self, d: typing.Dict):
        rs = inspect(self.__class__).relationships.keys()
        for k, v in d.items():
            if k not in rs:
                setattr(self, k, v)
            else:
                setattr(self, k + '_id', v['id'])

    def save(self):
        raise NotImplementedError('Mixing save cannot store versions')

    def update(self):
        raise NotImplementedError('Mixing update cannot store versions')


class Wallet(BaseModel):
    """Wallets of platform and borrowers"""

    __tablename__ = "wallets"
    __versioned__: dict = {}

    schema_class = WalletSchema  # marshmallow schema class
    message_class = wallets_pb2.Wallet  # proto message for this model

    currency_slug = Column(Text,
                           comment='Wallet currency slug',
                           nullable=False)

    address = Column(Text,
                     comment='Wallet address',
                     nullable=False)

    external_id = Column(Numeric,
                         comment='id from blockchain bridge serve for joining',
                         index=True,
                         nullable=False)

    transactions = Column(JSON,
                          comment='All transactions on current wallet',
                          default=None)

    active_transactions = Column(JSON,
                                 comment='Active trx on this wallet',
                                 default=None)

    is_platform = Column(Boolean,
                         comment='is platform wallet',
                         default=False,
                         nullable=False)

    on_monitoring = Column(Boolean,
                           comment='on monitoring',
                           default=True,
                           nullable=False,
                           index=True)
