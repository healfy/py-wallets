import abc
import typing
from decimal import Decimal
from decimal import ROUND_HALF_UP
from datetime import datetime
from datetime import timedelta
from flask import render_template
from sqlalchemy.orm import Session
from sqlalchemy.orm import Query

from wallets import app
from wallets import logger
from wallets.common import Wallet
from wallets.common import Transaction
from wallets.utils import send_message
from wallets.gateway.base import BaseGateway
from wallets.gateway import currencies_service_gw as c_gw
from wallets.gateway import blockchain_service_gw as b_gw
from wallets.gateway import transactions_service_gw
from wallets.gateway import exchanger_service_gw
from wallets.utils.consts import TransactionStatus

conf = app.config


class BaseMonitorClass(abc.ABC):
    """
    Base class for monitoring
    """
    timeout: int = conf['MONITORING_TRANSACTIONS_PERIOD']

    @classmethod
    def get_data(cls):
        """
        Simple method to get data for the processing
        """
        raise NotImplementedError('Method not implemented!')

    @classmethod
    def _execute(
            cls,
            session: Session
    ) -> typing.NoReturn:
        """
        Main method that contains all logic
        """
        raise NotImplementedError('Method not implemented!')

    @classmethod
    def process(
            cls,
            session: Session
    ) -> typing.NoReturn:
        """
        Method to release logic
        """
        try:
            cls._execute(session)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


class CompareRemains:
    """
    Class for compare remains from platform wallets and
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
        'chainlink': Decimal(conf['Chainlink']),
        'zilliqa': Decimal(conf['Zilliqa']),
        'usd-coin': Decimal(conf['USD-Coin'])
    }

    @classmethod
    def calc(
            cls,
            wallet: typing.Dict,
            usd_balance: Decimal,
            result: typing.List
    ) -> typing.NoReturn:

        if usd_balance <= cls.MIN_BALANCE_USD[wallet['currencySlug']]:
            result.append(
                {'currencySlug': wallet['currencySlug'],
                 'value': usd_balance,
                 'current': 'USD'
                 }
            )

    @classmethod
    def send_mail(
            cls,
            result: typing.Union[list, dict],
            warning: str = None
    ) -> typing.NoReturn:

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
    Class for save transaction if it necessary
    """

    @classmethod
    def save(
            cls,
            wallet: Wallet,
            request_object: typing.Dict,
            session: Session
    ) -> typing.NoReturn:

        trx = Transaction.from_dict(request_object)
        trx.wallet_id = wallet.id
        session.add(trx)
        session.commit()


class UpdateTrx:
    """
    Class for update transaction if it necessary
    """
    @classmethod
    def update(
            cls,
            wallet: Wallet,
            trx: typing.Dict,
            session: Session
    ) -> typing.NoReturn:

        session.query(Transaction).filter_by(
            wallet_id=wallet.id,
            status=TransactionStatus.NEW.value,
            address_from=trx['address_from'].lower(),
            currency_slug=trx['currency_slug'].lower(),
            hash=None,
        ).update({'hash': trx['hash'], 'value': trx['value']})

        session.commit()


class ValidateTRX:
    """
    Class to check transaction in base
    """

    @classmethod
    def exists(
            cls,
            trx_hash: str
    ) -> bool:
        return bool(
            Transaction.query.filter_by(hash=trx_hash.lower()).first()
        )

    @classmethod
    def is_input_trx(
            cls,
            address: str,
            wallet: Wallet
    ) -> bool:
        return wallet.address.lower() == address.lower()


class CheckWalletMonitor(BaseMonitorClass,
                         CompareRemains):
    """
    Class for monitoring platform wallets. If balance in USD
    <= MIN_BALANCE_USD, then sending message to owners of wallets
    If service currencies is unavailable, we send balance in wallet currency
    with attention, that currencies dont work correctly
    """
    timeout = conf['MONITORING_WALLETS_PERIOD']

    @classmethod
    def get_data(cls) -> typing.Tuple[dict, typing.Optional[dict]]:
        balances = b_gw.get_platform_wallets_balance()
        try:
            currencies = c_gw.get_currencies()
            rates = {c['slug']: c['rate'] for c in currencies}
        except Exception as exc:
            logger.warning(f"{cls.__class__.__name__} got {exc}")
            rates = None
        return balances, rates

    @classmethod
    def _execute(
            cls,
            session: Session
    ) -> typing.NoReturn:

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
    """
    This method monitors the wallet for input transactions and
    then stores them in the database
    """

    @classmethod
    def get_data(cls) -> Query:
        return Wallet.query.filter_by(on_monitoring=True, is_platform=False,
                                      is_active=True)

    @classmethod
    def _execute(
            cls,
            session: Session
    ) -> typing.NoReturn:

        for wallet in cls.get_data():
            trx_list = b_gw.get_transactions_list(
                wallet_address=wallet.address, external_id=wallet.external_id
            )
            for trx in trx_list:
                if not cls.exists(trx['hash']) \
                        and cls.is_input_trx(trx['address_to'], wallet):
                    cls.save(wallet, trx, session)


class CheckPlatformWalletsMonitor(CheckTransactionsMonitor,
                                  UpdateTrx):
    """
    This method monitors the wallet for input transactions and
    then stores them in the database. This condition for the exchange service
    transactions
    """
    time_delta_days = conf.get('DELTA_DAYS', 1)

    @classmethod
    def get_data(cls) -> Query:
        return Wallet.query.filter_by(on_monitoring=True, is_platform=True,
                                      is_active=True)

    @classmethod
    def _execute(
            cls,
            session: Session
    ) -> typing.NoReturn:

        for wallet in cls.get_data():
            trx_list = b_gw.get_exchanger_wallet_trx_list(
                slug=wallet.currency_slug,
                from_time=datetime.now() - timedelta(days=cls.time_delta_days)
            )
            for trx in trx_list:
                if not cls.exists(trx['hash']) and  \
                        cls.is_input_trx(trx['address_to'], wallet):
                    cls.update(wallet, trx, session)


class SendToExternalService(BaseMonitorClass, abc.ABC):

    gw: typing.Type['BaseGateway']

    @classmethod
    def _execute(
            cls,
            session: Session
    ) -> typing.NoReturn:

        if cls.get_data().first():
            cls.send_to_external_service(cls.get_data(), session=session)

    @classmethod
    def send_to_external_service(
            cls,
            data: Query,
            session: Session = None
    ) -> typing.NoReturn:

        raise NotImplementedError('Method not implemented!')


class SendToTransactionService(SendToExternalService):
    """
    Put all transactions to the external service "Transactions".
    Where they will monitor
    """
    gw = transactions_service_gw

    @classmethod
    def get_data(cls) -> Query:

        return Transaction.query.filter(
            Transaction.hash != None,
            Transaction.status == TransactionStatus.NEW.value,
        )

    @classmethod
    def send_to_external_service(
            cls,
            data: typing.Iterable[Transaction],
            session: Session = None
    ) -> typing.NoReturn:

        cls.gw.put_on_monitoring(data)
        for trx in data:
            trx.outer_update(session,
                             status=TransactionStatus.SENT.value)


class SendToExchangerService(SendToExternalService):
    """
    Put all confirmed input transactions associated with platform wallets to
    the external service "Exchanger"
    """

    gw = exchanger_service_gw

    @classmethod
    def get_data(cls) -> Query:

        return Transaction.query.join(
            Wallet, Wallet.id == Transaction.wallet_id
        ).filter(
            Transaction.hash != None,
            Transaction.uuid != None,
            Transaction.status == TransactionStatus.CONFIRMED.value,
            Wallet.is_platform == True,
        )

    @classmethod
    def send_to_external_service(
            cls,
            data: typing.Iterable[Transaction],
            session: Session = None
    ) -> typing.NoReturn:

        cls.gw.update_transactions(data)
        for trx in data:
            trx.outer_update(session,
                             status=TransactionStatus.REPORTED.value)


__TRANSACTIONS_TASKS__ = [SendToExchangerService,
                          SendToTransactionService,
                          CheckWalletMonitor]
