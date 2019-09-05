from marshmallow import fields
from marshmallow import Schema
from wallets.utils import DecimalStringField


class WalletSchema(Schema):
    currencySlug = fields.Str()
    value = DecimalStringField(missing='0')


class GetBalanceResponseSchema(Schema):
    balance = DecimalStringField(missing='0')

