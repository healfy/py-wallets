from marshmallow import Schema
from marshmallow import fields


class WalletSchema(Schema):
    id = fields.Int(required=False)
    address = fields.Str(required=False)
    currency_slug = fields.Str(required=False)
    is_platform = fields.Bool(required=False)
    external_id = fields.Int(required=False)
    transactions = fields.String(required=False)
    on_monitoring = fields.Boolean(required=False)

