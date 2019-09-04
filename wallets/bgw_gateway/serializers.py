from marshmallow import fields
from marshmallow import Schema
from wallets.utils import DecimalStringField
from wallets.common import TransactionSchema


class WalletSchema(Schema):
    currencySlug = fields.Str()
    value = DecimalStringField(missing='0')


class GetBalanceResponseSchema(Schema):
    balance = DecimalStringField(missing='0')


class TransactionResponseSchema(Schema):
    transaction = fields.Nested(TransactionSchema, missing=None)
