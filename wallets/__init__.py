import sys
from flask import Flask
from wallets.settings.config import conf
from wallets.logging import logger


sys.path.extend(
    ['/', '/app',
     'observer',
     'observer/rpc',
     '/app/rpc',
     '..',
     '../rpc',
     '/etc/observer']
)  # for docker

app = Flask('wallets')
app.config.update(conf)
