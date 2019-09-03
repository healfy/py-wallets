from marshmallow import fields
from marshmallow import Schema
from wallets.utils import DecimalStringField


class WalletSchema(Schema):
    currencySlug = fields.Str()
    value = DecimalStringField(missing='0')


class GetBalanceResponseSchema(Schema):
    balance = DecimalStringField(missing='0')


class TransactionSchema(Schema):
    id = fields.Integer()
    address_from = fields.Str(load_from='from', required=True)
    address_to = fields.Str(load_from='to')
    currency_slug = fields.Str(load_from='currencySlug', required=True)
    amount = DecimalStringField(load_from='value', required=True)
    hash = fields.Str(required=True)


class TransactionResponseSchema(Schema):
    transaction = fields.Nested(TransactionSchema, missing=None)
