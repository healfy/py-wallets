from marshmallow import Schema
from marshmallow import fields
from wallets.utils import StringLowerField
from wallets.utils import DecimalStringField


class WalletSchema(Schema):
    id = fields.Int(required=False)
    address = StringLowerField(required=True)
    currency_slug = StringLowerField(required=True)
    is_platform = fields.Bool(required=False)
    external_id = fields.Int(required=False)
    on_monitoring = fields.Boolean(required=False)


class TransactionSchema(Schema):
    id = fields.Integer()
    address_from = StringLowerField(data_key='from', required=True)
    address_to = StringLowerField(data_key='to')
    currency_slug = StringLowerField(data_key='currencySlug', required=True)
    value = DecimalStringField(data_key='value', required=True)
    hash = StringLowerField(required=True)
    wallet_id = fields.Integer(required=False)
    time = fields.Integer(required=False)

    def _deserialize(self, data, *args, **kwargs):
        ret = super()._deserialize(data, *args, **kwargs)
        ret.pop('time', None)
        return ret
