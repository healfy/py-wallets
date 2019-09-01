import sys
from google.cloud import logging as g_logging
from wallets.settings.config import conf
import logging
import os
import json

logger: logging.Logger = None


class WhitespaceRemovingFormatter(logging.Formatter):
    ws_stub = "\\n"

    def format(self, record):
        record.msg = record.msg.replace("\n", self.ws_stub)
        logmsg = super().format(record)
        return {
            'msg': logmsg,
            'args': json.dumps(record.args, default=str) or '',
        }


class TestFilter(logging.Filter):
    def filter(self, record):
        return not conf.get('TEST')


def init_logger():
    """
        init_logger connects to cloud logging if it's avaliable
    """
    global logger
    logger = logging.getLogger('wallets[{}]'.format(conf.get('ENV')))
    try:
        logger.setLevel(conf.get('LOGGING_LEVEL', 'INFO'))
        formatter = WhitespaceRemovingFormatter(
            '[%(asctime)s][%(levelname)s][%(module)s]: %(message)s'
        )
        if not conf.get('TEST') and not os.environ.get('TEST'):
            client = g_logging.Client(conf.get('PROJECT_NAME', None))
            handler = client.get_default_handler()
            logger.handlers = []
            logger.addHandler(handler)
            handler.setFormatter(formatter)
            handler.labels = {
                'app': 'wallets',
                'tier': 'backend',
                'track': conf.get('TRACK', 'no track'),
                'env': conf.get('ENV') or '',
            }
    except Exception as e:
        logger.error(f"failed getting cloud logger {e}")
    flt = TestFilter('test')
    logger.addFilter(flt)
    return logger


init_logger()


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    bind logger to system exceptions
    """

    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception",
                 exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception
