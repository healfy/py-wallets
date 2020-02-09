import os
import sys
import typing
from wallets.settings.config import conf
import logging
import logging.config


logger: typing.Optional[logging.Logger] = None

LOGFILE = os.path.join(f'{os.environ.get("LOGFILE", "")}', f'wallets[{conf.get("ENV")}].log')
dictLogConfig = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simple'
        },
        'file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'filename': LOGFILE,
            'formatter': 'verbose',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
        }
    },
    'loggers': {
        f'wallets[{conf.get("ENV")}]': {
            'handlers': ['console', 'file_handler'],
            'level': 'DEBUG',
        },
    }
}


def init_logger():
    """
        init_logger connects to cloud logging if it's avaliable
    """
    global logger
    logging.config.dictConfig(dictLogConfig)
    logger = logging.getLogger(f'wallets[{conf.get("ENV")}]')
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
