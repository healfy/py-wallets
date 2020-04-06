import os
import uuid
import pytz
import pytest
from decimal import Decimal
from datetime import datetime
from datetime import timedelta

from wallets.common import Wallet
from wallets.common import Transaction
from wallets.utils.consts import TransactionStatus

from wallets.rpc import blockchain_gateway_pb2

dbsession = None


def pytest_configure(config):
    print('*' * 10, 'CONFTEST SETUP', '*' * 10)
    # override settings from config.yaml
    os.environ['PGDATABASE'] = 'test_wallets'
    print('*' * 10, 'CONFTEST SETUP FINISHED', '*' * 10)


def transaction_response_result(value=1):
    return {
        'hash': f'{value}simple_hash',
        'value': Decimal(f'{value}'),
        'address_from': 'some_wallet_address',
        'currency_slug': 'bitcoin',
        'address_to': 'some_wallet_address'
    }


@pytest.fixture
def get_transactions_list_response_list():
    return [
        transaction_response_result(i) for i in range(1, 3)
    ]


@pytest.fixture
def transaction():
    trx = Transaction(**{
        'hash': str(uuid.uuid4()),
        'value': '123',
        'address_from': 'some_wallet_address',
        'currency_slug': 'bitcoin',
        'address_to': 'some_wallet_address',
        'uuid': str(uuid.uuid4()),
    })
    yield trx


@pytest.fixture
def transactions(wallet):
    trx = Transaction(**{
        'hash': str(uuid.uuid4()),
        'value': '123',
        'address_from': 'some_wallet_address',
        'currency_slug': 'bitcoin',
        'address_to': 'some_wallet_address',
        'wallet_id': wallet.id,
        'status': TransactionStatus.CONFIRMED.value,
        'confirmed_at': datetime.utcnow() - timedelta(days=1),
        'created_at': datetime.utcnow() - timedelta(days=1),
    })

    trx_2 = Transaction(**{
        'hash': str(uuid.uuid4()),
        'value': '123',
        'address_from': 'some_wallet_address',
        'currency_slug': 'bitcoin',
        'address_to': 'some_wallet_address',
        'wallet_id': wallet.id,
        'status': TransactionStatus.CONFIRMED.value,
        'confirmed_at': datetime.utcnow() - timedelta(days=1),
        'created_at': datetime.utcnow() - timedelta(days=1)
    })
    yield [trx, trx_2]


@pytest.fixture
def check_input_trxs_objects():
    time1_ = datetime.utcnow().replace(tzinfo=pytz.utc)

    address1 = f'{uuid.uuid4()}'
    address2 = f'{uuid.uuid4()}'

    wallet1 = Wallet(
        currency_slug='bitcoin',
        address=address1,
        external_id=223
    )

    wallet2 = Wallet(
        currency_slug='etherium',
        address=address2,
        external_id=21
    )

    trx1_response = {
        'transactions': [{
            'from': 'address1',
            'to': wallet1.address,
            'currencySlug': wallet1.currency_slug,
            'time': int(round(time1_.timestamp())),
            'value': "0.0001",
            'hash': f'{uuid.uuid4()}',
        }],
        'status': {
            'status': blockchain_gateway_pb2.ResponseStatus.Name(
                blockchain_gateway_pb2.PENDING)
        }
    }

    trx2_response = {
        'transactions': [{
            'from': 'address2',
            'to': wallet2.address,
            'currencySlug': wallet2.currency_slug,
            'time': int(round(time1_.timestamp())),
            'value': '0.021',
            'hash': f'{uuid.uuid4()}',
        }],
        'status': {
            'status': blockchain_gateway_pb2.ResponseStatus.Name(
                blockchain_gateway_pb2.SUCCESS)
        }
    }

    dct = {
        'trx1_resp': trx1_response,
        'trx2_resp': trx2_response,
        'wallet1': wallet1,
        'wallet2': wallet2,

    }
    yield dct


@pytest.fixture
def transaction_add_message():
    wallet1 = Wallet(
        currency_slug='bitcoin',
        address=str(uuid.uuid4()),
        external_id=223
    )

    yield {'trx': {
        'hash': str(uuid.uuid4()),
        'value': '123',
        'from_address': 'some_wallet_address',
        'currency': 'bitcoin',
        'wallet_address': str(wallet1.address),
        'uuid': str(uuid.uuid4()),
    },
        'wallet': wallet}


@pytest.fixture
def e_wallet():
    wallet = Wallet(
        currency_slug='bitcoin',
        address=uuid.uuid4(),
        external_id=223,
        is_platform=True,
    )

    yield wallet


@pytest.fixture
def exchanger_transaction(e_wallet):
    trx = Transaction(**{
        'hash': str(uuid.uuid4()),
        'value': '123',
        'address_from': 'some_wallet_address',
        'currency_slug': 'bitcoin',
        'address_to': e_wallet.address,
        'uuid': str(uuid.uuid4()),
        'wallet_id': e_wallet.id,
        'status': TransactionStatus.CONFIRMED.value,
    })

    yield trx


@pytest.fixture
def check_exch_trxs_objects():
    time1_ = datetime.utcnow().replace(tzinfo=pytz.utc)

    address1 = f'{uuid.uuid4()}'
    address2 = f'{uuid.uuid4()}'

    wallet1 = Wallet(
        currency_slug='bitcoin',
        address=address1,
        external_id=223,
        is_platform=True,
    )

    wallet2 = Wallet(
        currency_slug='etherium',
        address=address2,
        external_id=21,
        is_platform=True,
    )



    trx1 = Transaction(**{
        'value': '123',
        'address_from': 'address1',
        'currency_slug': wallet1.currency_slug,
        'address_to': wallet1.address,
        'uuid': str(uuid.uuid4()),
        'wallet_id': wallet1.id,
    })

    trx2 = Transaction(**{
        'value': '123',
        'address_from': 'address1',
        'currency_slug': wallet2.currency_slug,
        'address_to': wallet2.address,
        'uuid': str(uuid.uuid4()),
        'wallet_id': wallet2.id,
    })

    trx1_response = {
        'transactions': [{
            'from': trx1.address_from,
            'to': trx1.address_to,
            'currencySlug': trx1.currency_slug,
            'time': int(round(time1_.timestamp())),
            'value': trx1.value,
            'hash': f'{uuid.uuid4()}',
        }],
        'status': {
            'status': blockchain_gateway_pb2.ResponseStatus.Name(
                blockchain_gateway_pb2.SUCCESS)
        }
    }

    trx2_response = {
        'transactions': [{
            'from': trx2.address_from,
            'to': trx2.address_to,
            'currencySlug': trx2.currency_slug,
            'time': int(round(time1_.timestamp())),
            'value': trx2.value,
            'hash': f'{uuid.uuid4()}',
        }],
        'status': {
            'status': blockchain_gateway_pb2.ResponseStatus.Name(
                blockchain_gateway_pb2.SUCCESS)
        }
    }

    dct = {
        'trx1_resp': trx1_response,
        'trx2_resp': trx2_response,
        'wallet1': wallet1,
        'wallet2': wallet2,

    }
    yield dct


@pytest.fixture
def transaction_new():
    trx = Transaction(**{
        'hash': str(uuid.uuid4()),
        'value': '123',
        'address_from': 'some_wallet_address',
        'currency_slug': 'bitcoin',
        'address_to': 'some_wallet_address',
        'uuid': str(uuid.uuid4()),
    })
    dbsession.add(trx)
    dbsession.commit()
    yield trx


@pytest.fixture
def transaction_add_message_new(transaction_new):
    wallet1 = Wallet(
        currency_slug='bitcoin',
        address=transaction_new.address_to,
        external_id=223
    )
    dbsession.add_all([wallet1])
    dbsession.commit()

    yield {'trx': {
        'hash': transaction_new.hash,
        'value': '123',
        'from_address': 'some_wallet_address',
        'currency': 'bitcoin',
        'wallet_address': str(wallet1.address),
        'uuid': str(uuid.uuid4()),
    },
        'wallet': wallet}
