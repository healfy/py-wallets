# auto-generated snapshot
from peewee import *
import datetime
import peewee


snapshot = Snapshot()


@snapshot.append
class Wallet(peewee.Model):
    created_at = DateTimeField(default=datetime.datetime.now, index=True)
    updated_at = DateTimeField(default=datetime.datetime.now)
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
    created_at = DateTimeField(default=datetime.datetime.now, index=True)
    updated_at = DateTimeField(default=datetime.datetime.now)
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


def forward(old_orm, new_orm):
    wallet = new_orm['wallet']
    transaction = new_orm['transaction']
    return [
        # Apply default value datetime.datetime(2020, 3, 29, 18, 11, 17, 264681) to the field wallet.created_at
        wallet.update({wallet.created_at: datetime.datetime(2020, 3, 29, 18, 11, 17, 264681)}).where(wallet.created_at.is_null(True)),
        # Apply default value datetime.datetime(2020, 3, 29, 18, 11, 17, 264777) to the field wallet.updated_at
        wallet.update({wallet.updated_at: datetime.datetime(2020, 3, 29, 18, 11, 17, 264777)}).where(wallet.updated_at.is_null(True)),
        # Apply default value datetime.datetime(2020, 3, 29, 18, 11, 17, 265081) to the field transaction.created_at
        transaction.update({transaction.created_at: datetime.datetime(2020, 3, 29, 18, 11, 17, 265081)}).where(transaction.created_at.is_null(True)),
        # Apply default value datetime.datetime(2020, 3, 29, 18, 11, 17, 265174) to the field transaction.updated_at
        transaction.update({transaction.updated_at: datetime.datetime(2020, 3, 29, 18, 11, 17, 265174)}).where(transaction.updated_at.is_null(True)),
    ]
