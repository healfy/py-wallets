# auto-generated snapshot
from peewee import *
import datetime
import peewee


snapshot = Snapshot()


@snapshot.append
class Wallet(peewee.Model):
    currency_slug = CharField(max_length=255)
    address = CharField(max_length=255)
    external_id = IntegerField(index=True)
    is_platform = BooleanField(default=False)
    on_monitoring = BooleanField(default=True)
    is_active = BooleanField(default=True)
    class Meta:
        table_name = "wallet"


@snapshot.append
class Transaction(peewee.Model):
    status = IntegerField(default=1, index=True)
    hash = CharField(max_length=255, null=True, unique=True)
    address_from = CharField(max_length=255)
    address_to = CharField(max_length=255)
    currency_slug = CharField(max_length=255)
    value = DecimalField(auto_round=False, decimal_places=10, max_digits=20, rounding='ROUND_HALF_EVEN')
    is_fee_trx = BooleanField(default=False)
    confirmed_at = DateField(null=True)
    wallet = snapshot.ForeignKeyField(backref='transactions', index=True, model='wallet')
    uuid = UUIDField(null=True, unique=True)
    class Meta:
        table_name = "transaction"


