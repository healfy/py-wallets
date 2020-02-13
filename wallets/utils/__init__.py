import pytz
import typing
import requests
from decimal import Decimal
from datetime import datetime
from marshmallow import fields
from google.protobuf import timestamp_pb2
from wallets.settings.config import conf


def get_msg_timestamp_from_datetime(value):
    msg = timestamp_pb2.Timestamp()
    if value is not None:
        msg.FromDatetime(value.astimezone(pytz.utc).replace(tzinfo=None))
    return msg


class DecimalStringField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        return str(value) if value is not None else None

    def _deserialize(self, value, attr, obj, **kwargs):
        if not value or value == 'None':
            return None
        return Decimal(value)


class DatetimeField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        return get_msg_timestamp_from_datetime(value)

    def _deserialize(self, value, attr, obj, **kwargs):
        if value is not None and value != 'None' and type(value) != str:
            return value.ToDatetime().replace(tzinfo=pytz.utc)
        elif type(value) == str:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=pytz.utc)
        return value


class StringLowerField(fields.String):

    def _serialize(self, value, attr, obj, **kwargs):
        return super()._serialize(value, attr, obj, **kwargs).lower()

    def _deserialize(self, value, attr, data, **kwargs):
        return super()._deserialize(value, attr, data, **kwargs).lower()


def send_message(html, subject):

    url = f'https://api.mailgun.net/v3/{conf["MAIL_DOMAIN"]}/messages'
    auth = ('api', f'{conf["MAIL_PASSWORD"]}')
    data = {
        'from': f'Mailgun User <{conf["MAIL_USERNAME"]}>',
        'to': conf["RECIPIENTS"],
        'subject': subject,
        'html': html,
    }
    response = requests.post(url, auth=auth, data=data)
    response.raise_for_status()


def simple_generator(iterable_object):
    for obj in iterable_object:
        yield obj


def get_existing_wallet(_id: int = None, address: str = None
                        ) -> typing.Any:
    from wallets.common import models

    if _id is not None:
        return models.Wallet.query.filter_by(external_id=_id).first()
    if address is not None:
        return models.Wallet.query.filter(models.Wallet.address == address).first()
    raise ValueError(
        'Get wallet error: expect at least one of id, address parameters.'
    )


def get_exchanger_wallet(address: str, slug: str):
    from wallets.common import models
    wallet = models.Wallet.query.filter_by(
        address=address, currency_slug=slug).first()
    if not wallet:
        raise ValueError(
            f'Get wallet error: the wallet {address} ans slug {slug} is '
            f'not found.'
        )
    return wallet
