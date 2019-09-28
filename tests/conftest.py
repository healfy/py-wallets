import os
import uuid
import pytest
from decimal import Decimal
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine

from wallets import db
from wallets import app
from wallets import start_engine
from wallets.common import Wallet
from wallets.common import Transaction
from wallets.common.models import Base
from wallets.settings.config import conf
from wallets.shared.logging import init_logger

dbsession = None


def pytest_configure(config):
	print('*' * 10, 'CONFTEST SETUP', '*' * 10)
	# override settings from config.yaml
	conf['LOGGING_LEVEL'] = 'WARNING'
	conf['USE_BLOCKCHAIN_GW'] = False
	if config.getoption('pg_string', None):
		conf['PGSTRING'] = config.getoption('pg_string')

	init_logger()
	from wallets.shared.logging import logger
	logger.handlers = []
	start_engine(restart=True)

	engine = create_engine(
		conf['PGSTRING'],
		echo=conf.get('DB_DEBUG')
	)
	app.config['SQLALCHEMY_DATABASE_URI'] = engine.url
	db = SQLAlchemy(app)
	global dbsession
	dbsession = db.session
	# using fresh main db
	engine.execute('drop schema if exists public cascade;')
	engine.execute('create schema public;')
	Base.metadata.drop_all(engine)
	Base.metadata.create_all(engine)
	print('*' * 10, 'CONFTEST SETUP FINISHED', '*' * 10)


def pytest_addoption(parser):
	parser.addoption("--runslow", action="store_true",
					 default=False, help="run slow tests")
	parser.addoption("--pg_string",
					 default='postgresql:///test_wallets?user={}'.format(
						 os.environ.get('USERNAME', os.environ.get('USER'))),
					 help="DB connection string")


def pytest_collection_modifyitems(config, items):
	if config.getoption("--runslow"):
		return
	skip_slow = pytest.mark.skip(reason="need --runslow option to run")
	for item in items:
		if "slow" in item.keywords:
			item.add_marker(skip_slow)


@pytest.fixture
def session_fixture():
	yield db.session


def delete_all():
	dbsession.query(Transaction).delete()
	dbsession.query(Wallet).delete()
	dbsession.commit()


@pytest.fixture
def wallet():
	wallet = Wallet(
		currency_slug='bitcoin',
		address=uuid.uuid4(),
		external_id=223
	)
	dbsession.add(wallet)
	dbsession.commit()
	dbsession.refresh(wallet)
	yield wallet


@pytest.fixture
def wallet_req_object_dict():
	return {
		'external_id': 1,
		'is_platform': True,
		'address': str(uuid.uuid4()),
		'currency_slug': 'bitcoin',
	}


@pytest.fixture
def get_balance_by_slug_request():
	return 'bitcoin'


@pytest.fixture
def get_balance_by_slug_response():
	return {
		'balance': '12345'
	}


@pytest.fixture
def get_balance_response_object(get_balance_by_slug_response):
	return Decimal(get_balance_by_slug_response['balance'])


def wallet_msg(slug, value='1234'):
	return {'currencySlug': slug, 'value': value}


def wallet_result_msg(slug, value='1234'):
	return {'currencySlug': slug, 'value': Decimal(value)}


@pytest.fixture
def platform_balances_response():
	return {
		'wallets': [wallet_msg(slug) for slug in ['bitcoin', 'eth', 'binance']]
	}


@pytest.fixture
def platform_balances_response_object():
	return [wallet_result_msg(slug) for slug in ['bitcoin', 'eth', 'binance']]


@pytest.fixture
def get_transactions_request():
	return {
		'external_id': 233,
		'wallet_address': str(uuid.uuid4())
	}


def transaction_response_data(value=1):
	return {
		'from': 'some_wallet_address',
		'to': 'some_wallet_address',
		'currencySlug': 'bitcoin',
		'value': f'{value}',
		'hash': f'{value}simple_hash'
	}


@pytest.fixture
def get_transactions_list_response_data():
	return {
		'transactions': [transaction_response_data(value=i) for i in
						 range(1, 3)]
	}


def transaction_response_result(value=1):
	return {
		'hash': f'{value}simple_hash',
		'value': Decimal(f'{value}'),
		'is_output': False,
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
		'is_output': False,
		'address_from': 'some_wallet_address',
		'currency_slug': 'bitcoin',
		'address_to': 'some_wallet_address'
	})
	dbsession.add(trx)
	dbsession.commit()
	yield trx


@pytest.fixture
def transactions(wallet):
	trx = Transaction(**{
		'hash': str(uuid.uuid4()),
		'value': '123',
		'is_output': False,
		'address_from': 'some_wallet_address',
		'currency_slug': 'bitcoin',
		'address_to': 'some_wallet_address',
		'wallet_id': wallet.id,
		'transfer_status': 2,
		'confirmed_at': datetime.now()
	})

	trx_2 = Transaction(**{
		'hash': str(uuid.uuid4()),
		'value': '123',
		'is_output': False,
		'address_from': 'some_wallet_address',
		'currency_slug': 'bitcoin',
		'address_to': 'some_wallet_address',
		'wallet_id': wallet.id,
		'transfer_status': 2,
		'confirmed_at': datetime.now()
	})
	dbsession.add_all([trx, trx_2])
	dbsession.commit()
	yield [trx, trx_2]
