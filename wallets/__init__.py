import sys
import os
from contextlib import contextmanager

from flask import Flask
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy

from wallets.settings.config import conf
from wallets.shared.logging import logger
from wallets.gateway import start_remote_gateways
from wallets.common import BaseModel

sys.path.extend(
    ['/', '/app',
     'observer',
     'observer/rpc',
     '/app/rpc',
     '..',
     '../rpc',
     '/etc/observer']
)  # for docker

DBSession = scoped_session(sessionmaker())
engine = None
db = None

app = Flask('wallets')
app.config.update(conf)


def start_engine(restart=False):
    global engine
    global db
    from sqlalchemy.engine.url import URL, make_url
    connect_url = make_url(
     conf['PGSTRING']) if conf['PGSTRING'] is not None and conf[
     'PGSTRING'] != 'None' else URL(
      'postgresql',
      username=os.getenv('PGUSER'),
      host=os.getenv('PGHOSTADDR'),
      password=os.getenv('PGPASSWORD'),
      database=os.getenv('PGDATABASE', 'postgres'),
     )
    app.config['SQLALCHEMY_DATABASE_URI'] = connect_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)

    if engine is None or restart is True:
        engine = create_engine(
            connect_url,
            echo=conf.get('DB_DEBUG'),
            logging_name=logger.name,
        )
    DBSession.remove()
    DBSession.configure(bind=engine)
    BaseModel.set_session(DBSession)
    logger.info('DB connection established')


def session_maker() -> scoped_session:
    if not engine:
        start_engine()
    return DBSession


start_engine()
BaseModel.set_session(DBSession)
start_remote_gateways()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = db.session
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
