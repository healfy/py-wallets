from marshmallow import Schema
from marshmallow import fields
from wallets.utils import DecimalStringField


class WalletSchema(Schema):
    id = fields.Int(required=False)
    address = fields.Str(required=True)
    currency_slug = fields.Str(required=True)
    is_platform = fields.Bool(required=False)
    external_id = fields.Int(required=False)
    on_monitoring = fields.Boolean(required=False)


class TransactionSchema(Schema):
    id = fields.Integer()
    address_from = fields.String(data_key='from', required=True)
    address_to = fields.String(data_key='to')
    currency_slug = fields.String(data_key='currencySlug', required=True)
    value = DecimalStringField(data_key='value', required=True)
    hash = fields.String(required=True)
    wallet_id = fields.Integer(required=False)
