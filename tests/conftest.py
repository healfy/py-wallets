import pytest
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
    engine.execute("create extension if not exists hstore;")
    print('*' * 10, 'CONFTEST SETUP FINISHED', '*' * 10)


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true",
                     default=False, help="run slow tests")


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
def current_datetime():
    return datetime.now()
