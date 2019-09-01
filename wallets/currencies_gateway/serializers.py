from marshmallow import Schema, fields
from wallets.utils import DatetimeField, DecimalStringField


class CurrencyCoefficientSchema(Schema):
    days = fields.Int(required=True)
    collateral_coefficient = DecimalStringField(required=True)
    mandatory_coefficient = DecimalStringField(required=True)
    warning_coefficient = DecimalStringField(required=True)
    datetime = DatetimeField()


class CurrencyRateSchema(Schema):
    name = fields.Str()
    slug = fields.Str(required=True)
    symbol = fields.Str()
    fullname = fields.Str()
    rate = DecimalStringField(required=True)
    coefficients = fields.Nested(CurrencyCoefficientSchema, many=True,
                                 missing=tuple())
    datetime = DatetimeField()
