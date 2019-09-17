import abc
import typing
import traceback
from decimal import Decimal
from decimal import ROUND_HALF_UP
from flask import render_template

from wallets.settings.config import conf
from wallets import logger
from wallets import session_scope
from wallets.common import Wallet
from wallets.common import Transaction
from wallets.utils import send_message
from wallets.utils import simple_generator
from wallets.gateway import currencies_service_gw as c_gw
from wallets.gateway import blockchain_service_gw as b_gw


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


class CompareRemainsMixin:
    """
    Mixin Class for compare remains from platform wallets and
    sending email if it necessary
    """

    MIN_BALANCE_USD: dict = {
        'ethereum': Decimal(conf['Ethereum']),
        'bitcoin': Decimal(conf['Bitcoin']),
        'binance-coin': Decimal(conf['Binance-coin']),
        'trueusd': Decimal(conf['TrueUSD']),
        'omisego': Decimal(conf['OmiseGo']),
        'basic-attention-token': Decimal(conf['Basic-Attention-Token']),
        'holo': Decimal(conf['Holo']),
        'chainlink': Decimal(conf['min_Chainlink']),
        'zilliqa': Decimal(conf['Zilliqa']),
        'usd-coin': Decimal(conf['USD-Coin'])
    }

    @classmethod
    def calc(cls, wallet: typing.Dict, usd_balance: Decimal,
             result: typing.List):
        if usd_balance <= cls.MIN_BALANCE_USD[wallet['currencySlug']]:
            result.append(
                {'currencySlug': wallet['currencySlug'],
                 'value': usd_balance,
                 'current': 'USD'
                 }
            )

    @classmethod
    def send_mail(cls, result: typing.List, warning: str = None):
        msg = 'Actual balances of platforms'
        if result:
            context = dict(wallets=result)
            context['warning'] = warning
            html = render_template(
                conf['MONITORING_TEMPLATE'], **context
            )
            send_message(html, msg)


class SaveTrx:
    """
    Mixin Class for save transaction if it necessary
    """

    @classmethod
    def save(cls, wallet: Wallet, request_object: typing.Dict):
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


class ValidateTRX:
    """
    Mixin Class to check transaction in base
    """

    @classmethod
    def exists(cls, trx_hash: str) -> bool:
        return bool(
            Transaction.query.filter_by(hash=trx_hash).first()
        )

    @classmethod
    def is_input_trx(cls, address: str, wallet: Wallet):
        return wallet.address == address


class CheckWalletMonitor(BaseMonitorClass,
                         CompareRemainsMixin):
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
        wallets, rates = cls.get_data()

        if not rates:
            for wallet in wallets:
                wallet['current'] = wallet['currencySlug']
            cls.send_mail(wallets,
                          warning='Attention, service currencies is unavailable'
                          )
        else:
            result = []
            for wallet in wallets:
                rate = rates.get(wallet['currencySlug'])

                usd_balance = (
                        Decimal(rate) * Decimal(wallet['value'])
                ).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP) \
                    if rate else int(bool(rate))

                cls.calc(wallet, usd_balance, result)

            cls.send_mail(wallets)


class CheckTransactionsMonitor(BaseMonitorClass,
                               SaveTrx,
                               ValidateTRX):

    @classmethod
    def get_data(cls):
        return simple_generator(
            Wallet.query.filter_by(on_monitoring=True).all()
        )

    @classmethod
    def _execute(cls):
        for wallet in cls.get_data():
            trx_list = b_gw.get_transactions_list(
                wallet_address=wallet.address, external_id=wallet.external_id
            )
            for trx in simple_generator(trx_list):
                if not cls.exists(trx['hash']) \
                        and cls.is_input_trx(trx['to'], wallet):
                    cls.save(wallet, trx)
