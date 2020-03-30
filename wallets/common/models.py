import typing
import peewee
from datetime import datetime

from wallets import db
from wallets.utils.consts import TransactionStatus


class BaseModel(peewee.Model):

    created_at = peewee.DateTimeField(
        verbose_name='Datetime of creating object',
        default=datetime.now,
        index=True)

    updated_at = peewee.DateTimeField(
        verbose_name='Datetime of updating object',
        default=datetime.now,
    )

    class Meta:
        database = db

    def save(self, force_insert=False, only=None):
        self.updated_at = datetime.now()
        return super().save(force_insert=force_insert, only=only)


class Wallet(BaseModel):

    currency_slug = peewee.CharField(
        verbose_name='Wallet currency slug'
    )

    address = peewee.CharField(
        verbose_name='Wallet address'
    )

    external_id = peewee.IntegerField(
        verbose_name='id from deposits bridge serve for joining',
        index=True,
    )

    is_platform = peewee.BooleanField(
        verbose_name='is platform wallet',
        default=False)

    on_monitoring = peewee.BooleanField(
        verbose_name='on monitoring',
        default=True,
    )
    is_active = peewee.BooleanField(
        verbose_name='wallet on work',
        default=True,
    )


class Transaction(BaseModel):
    """BlockChain transaction"""

    ACTIVE_STATUTES = (
        TransactionStatus.NEW.value,
        TransactionStatus.SUCCESSFUL.value,
        TransactionStatus.PENDING.value,
    )

    STATUTES = tuple(
        [(v.value, k) for k, v in TransactionStatus.members_items()]
    )

    status = peewee.IntegerField(
        index=True,
        default=TransactionStatus.NEW.value,
        choices=STATUTES,
        verbose_name='current transaction status'
    )

    hash = peewee.CharField(
        null=True,
        verbose_name='transaction hash',
        unique=True
    )

    address_from = peewee.CharField(
        verbose_name='initiator of transaction',
    )

    address_to = peewee.CharField(
        verbose_name='to whom transfer transaction',
    )

    currency_slug = peewee.CharField(
        verbose_name='transaction currency',
    )

    value = peewee.DecimalField(
        verbose_name='transactions amount',
        decimal_places=10,
        max_digits=20
    )

    is_fee_trx = peewee.BooleanField(
        verbose_name='Is it transaction to send fee on wallet',
        default=False)

    confirmed_at = peewee.DateField(
        null=True,
        verbose_name='time in that transaction confirmed'
    )

    wallet = peewee.ForeignKeyField(
        Wallet,
        verbose_name='wallet',
        related_name='transactions'
    )

    uuid = peewee.UUIDField(
        unique=True,
        null=True,
        verbose_name='Additional identification for exchanger service'
    )

    def _as_message_dict(self) -> typing.Dict:
        return {
            'to': self.address_to,
            'from': self.address_from,
            'currencySlug': self.currency_slug,
            'value': f'{self.value}',
            'hash': self.hash,
        }

    def set_confirmed(self) -> typing.NoReturn:
        self.status = TransactionStatus.CONFIRMED.value
        self.confirmed_at = datetime.now()
        self.save()
