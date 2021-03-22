import pytz
from functools import wraps
from decimal import Decimal
from datetime import datetime
from marshmallow import fields
from aiohttp import ClientSession
from google.protobuf import timestamp_pb2
from wallets import objects
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


async def send_message(html, subject):

    url = f'https://api.mailgun.net/v3/{conf["MAIL_DOMAIN"]}/messages'
    auth = ('api', f'{conf["MAIL_PASSWORD"]}')
    data = {
        'from': f'Mailgun User <{conf["MAIL_USERNAME"]}>',
        'to': conf["RECIPIENTS"],
        'subject': subject,
        'html': html,
    }
    async with ClientSession() as session:
        async with session.post(url, auth=auth, data=data) as resp:
            response = await resp.json()
            response.raise_for_status()


async def get_exchanger_wallet(address: str, slug: str):
    from wallets.common import models
    wallet = await objects.get(models.Wallet,
                               address=address,
                               currency_slug=slug)
    return wallet


def nested_commit_on_success(func):
    @wraps(func)
    async def _nested_commit_on_success(*args, **kwargs):
        async with objects.atomic():
            return await func(*args, **kwargs)
    return _nested_commit_on_success
