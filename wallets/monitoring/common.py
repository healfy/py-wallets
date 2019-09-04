import abc
import traceback
from decimal import Decimal
from decimal import ROUND_HALF_UP
from flask import render_template

from wallets.settings.config import conf
from wallets import logger
from wallets import session_scope
from wallets.common import Wallet
from wallets.common import Transaction
from wallets.common import TransactionSchema
from wallets.utils import send_message
from wallets.gateway import currencies_service_gw as c_gw
from wallets.gateway import blockchain_service_gw as b_gw


class SaveTrxMixin:

    @classmethod
    def save(cls, wallet: Wallet, request_object: TransactionSchema):
        with session_scope() as session:
            try:
                trx = Transaction.from_dict(request_object)
                session.add(trx)
                session.commit()
                wallet.transaction_id = trx.id
                session.commit()
            except Exception as e:
                logger.error(
                    f"Class {cls.__name__} failed with {e.__class__.__name__}: "
                    f"{e}. {traceback.format_stack()}")
                session.rollback()
            finally:
                session.close()


class BaseMonitorClass(abc.ABC):
    """
    Base class for monitoring
    """

    @classmethod
    def get_data(cls):
        """
        Simple method to get data for the processing
        """
        raise NotImplementedError('Method not implemented!')

    @classmethod
    def _execute(cls):
        """
        Main method that contains all logic
        """
        raise NotImplementedError('Method not implemented!')

    @classmethod
    def process(cls):
        """
        Method to release logic
        """
        logger.info(f"{cls.__name__} group task started.")
        try:
            cls._execute()
        except Exception as e:
            logger.error(
                f"Class {cls.__name__} failed with {e.__class__.__name__}: "
                f"{e}. {traceback.format_stack()}")


class CheckWalletMonitor(BaseMonitorClass):
    """
    Class for monitoring platform wallets. If balance in USD
    <= MIN_BALANCE_USD, then sending message to owners of wallets
    If service currencies is unavailable, we send balance in wallet currency
    with attention, that currencies dont work correctly
    """

    @classmethod
    def get_data(cls):
        balances = b_gw.get_platform_wallets_balance()
        try:
            currencies = c_gw.get_currencies()
            rates = {c['slug']: c['rate'] for c in currencies}
        except Exception as exc:
            logger.warning(f"{cls.__class__.__name__} got {exc}")
            rates = None
        return balances, rates

    @classmethod
    def _execute(cls):
        msg = 'Actual balances of platforms'
        wallets, rates = cls.get_data()

        if not rates:
            for wallet in wallets:
                wallet['current'] = wallet['currencySlug']
            context = dict(wallets=wallets)
            context['warning'] = 'Attention, service currencies is unavailable'
            html = render_template(conf['MONITORING_TEMPLATE'], **context)
            send_message(html, msg)
        else:
            result = []
            for wallet in wallets:
                rate = rates.get(wallet['currencySlug'])

                usd_balance = (
                        Decimal(rate) * Decimal(wallet['value'])
                ).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP) \
                    if rate else int(bool(rate))

                if usd_balance <= Decimal(conf['MIN_BALANCE_USD']):
                    result.append(
                        {'currencySlug': wallet['currencySlug'],
                         'value': usd_balance,
                         'current': 'USD'
                         }
                    )
            if result:
                context = dict(wallets=result)
                html = render_template(
                    conf['MONITORING_TEMPLATE'], **context
                )
                send_message(html, msg)


class CheckTransactionsMonitor(BaseMonitorClass, SaveTrxMixin):

    @classmethod
    def get_data(cls):
        return Wallet.query.filter(on_monitoring=True).all()

    @classmethod
    def _execute(cls):
        wallets = cls.get_data()
