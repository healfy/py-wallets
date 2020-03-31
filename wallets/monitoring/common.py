import abc
import typing
from decimal import Decimal
from decimal import ROUND_HALF_UP
from datetime import datetime
from datetime import timedelta
from sqlalchemy.orm import Session
from sqlalchemy.orm import Query
from redis import StrictRedis

from wallets import app
from wallets import logger
from wallets import objects
from wallets.common import Wallet
from wallets.common import Transaction
from wallets.utils import send_message
from wallets.utils import nested_commit_on_success
from wallets.utils.locks import nowait_lock
from wallets.utils.locks import connect_redis
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
    counter: int = 0  # for logging
    manager = objects

    @classmethod
    async def get_data(cls):
        """
        Simple method to get data for the processing
        """
        raise NotImplementedError('Method not implemented!')

    @classmethod
    async def _execute(
            cls,
    ) -> typing.NoReturn:
        """
        Main method that contains all logic
        """
        raise NotImplementedError('Method not implemented!')

    @classmethod
    @nested_commit_on_success
    async def process(
            cls,
    ) -> typing.NoReturn:
        """
        Method to release logic
        """
        try:
            await cls._execute()
        except Exception as e:
            raise e
        finally:
            cls.counter = 0


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
    async def send_mail(
            cls,
            result: typing.Union[list, dict],
            warning: str = None
    ) -> typing.NoReturn:

        msg = 'Actual balances of platforms'
        if result:
            context = dict(wallets=result)
            context['warning'] = warning
            await send_message('', msg)


class SaveTrx:
    """
    Class for save transaction if it necessary
    """
    manager: objects

    @classmethod
    async def save(
            cls,
            wallet: Wallet,
            request_object: typing.Dict,
    ) -> typing.NoReturn:
        trx = await cls.manager.create(Transaction, request_object)
        trx.wallet_id = wallet.id
        await cls.manager.update(trx)


class UpdateTrx:
    """
    Class for update transaction if it necessary
    """

    manager: objects

    @classmethod
    async def update(
            cls,
            wallet: typing.Type['Wallet'],
            trx: typing.Dict,
    ) -> int:

        trx: Transaction = await cls.manager.get(
            Transaction,
            wallet_id=wallet.id,
            status=TransactionStatus.NEW.value,
            address_from=trx['address_from'].lower(),
            currency_slug=trx['currency_slug'].lower(),
            hash=None
        )
        trx.hash = trx['hash']
        trx.value = trx['value']
        return int(bool(await cls.manager.update(trx)))


class ValidateTRX:
    """
    Class to check transaction in base
    """
    manager: objects

    @classmethod
    async def exists(
            cls,
            trx_hash: str
    ) -> bool:
        return await cls.manager.exists(Transaction, hash=trx_hash)

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
    async def get_data(cls) -> typing.Tuple[dict, typing.Optional[dict]]:
        balances = await b_gw.get_platform_wallets_balance()
        try:
            currencies = await c_gw.get_currencies()
            rates = {c['slug']: c['rate'] for c in currencies}
        except Exception as exc:
            logger.warning(f"{cls.__class__.__name__} got {exc}")
            rates = None
        return balances, rates

    @classmethod
    async def _execute(
            cls,
    ) -> typing.NoReturn:

        wallets, rates = await cls.get_data()

        if not rates:
            for wallet in wallets:
                wallet['current'] = wallet['currencySlug']

            await cls.send_mail(
                wallets,
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

            await cls.send_mail(result)


class CheckTransactionsMonitor(BaseMonitorClass,
                               SaveTrx,
                               ValidateTRX):
    """
    This method monitors the wallet for input transactions and
    then stores them in the database
    """

    @classmethod
    async def get_data(cls) -> Query:
        return await cls.manager.get_all(Wallet,
                                         on_monitoring=True,
                                         is_platform=False,
                                         is_active=True)

    @classmethod
    async def _execute(
            cls,
    ) -> typing.NoReturn:

        for wallet in await cls.get_data():
            trx_list = await b_gw.get_transactions_list(
                wallet_address=wallet.address, external_id=wallet.external_id
            )
            for trx in trx_list:
                if not await cls.exists(trx['hash']) \
                        and cls.is_input_trx(trx['address_to'], wallet):
                    await cls.save(wallet, trx)
                    cls.counter += 1
            logger.info(f'{cls.__name__} saved {cls.counter} '
                        f'transactions')


class CheckPlatformWalletsMonitor(CheckTransactionsMonitor,
                                  UpdateTrx):
    """
    This method monitors the wallet for input transactions and
    then stores them in the database. This condition for the exchange service
    transactions
    """
    time_delta_days = conf.get('DELTA_DAYS', 1)

    @classmethod
    async def get_data(cls) -> Query:
        return await cls.manager.get_all(Wallet,
                                         on_monitoring=True,
                                         is_platform=True,
                                         is_active=True)

    @classmethod
    async def _execute(
            cls,
    ) -> typing.NoReturn:

        for wallet in await cls.get_data():
            trx_list = await b_gw.get_exchanger_wallet_trx_list(
                slug=wallet.currency_slug,
                from_time=datetime.now() - timedelta(days=cls.time_delta_days)
            )
            for trx in trx_list:
                if not await cls.exists(trx['hash']) and \
                        cls.is_input_trx(trx['address_to'], wallet):
                    cls.counter += await cls.update(wallet, trx)

        logger.info(f'{cls.__name__} updated {cls.counter} '
                    f'transactions')


class SendToExternalService(BaseMonitorClass, abc.ABC):
    gw: typing.Type['BaseGateway']
    redis: StrictRedis = connect_redis()

    @classmethod
    async def _execute(
            cls,
    ) -> typing.NoReturn:
        if cls.get_data().first():
            cls.send_to_external_service(cls.get_data(), redis=cls.redis)

    @classmethod
    def send_to_external_service(
            cls,
            data: Query,
            redis: StrictRedis = None
    ) -> typing.NoReturn:
        raise NotImplementedError('Method not implemented!')

    @classmethod
    def get_status_from_resp(cls, response: dict):
        return cls.gw.MODULE.ResponseStatus.Value(
            response[cls.gw.response_attr]['status'])


class SendToTransactionService(SendToExternalService):
    """
    Put all transactions to the external service "Transactions".
    Where they will monitor and also are sent back
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
            session: Session = None,
            redis: StrictRedis = None,
    ) -> typing.NoReturn:
        for trx in data:
            key = Transaction.lock_name_by_id(trx.id)
            with nowait_lock(redis) as locker:
                if locker.lock(key, blocking=True):

                    try:
                        resp = cls.gw.put_on_monitoring([trx])
                    except cls.gw.EXC_CLASS as exc:
                        logger.error(f'{cls.__name__} got exc from '
                                     f'TransactionService {exc}')
                        continue

                    if cls.get_status_from_resp(
                            resp) in cls.gw.ALLOWED_STATUTES:
                        trx.outer_update(session,
                                         status=TransactionStatus.SENT.value)
                        cls.counter += 1
            logger.info(f'{cls.__name__} sent {cls.counter} '
                        f'transactions')


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
            session: Session = None,
            redis: StrictRedis = None,
    ) -> typing.NoReturn:
        for trx in data:
            key = Transaction.lock_name_by_id(trx.id)
            with nowait_lock(redis) as locker:
                if locker.lock(key):
                    try:
                        resp = cls.gw.update_transactions([trx])
                    except cls.gw.EXC_CLASS as exc:
                        logger.error(f'{cls.__name__} got exc from '
                                     f'ExchangerService {exc}')
                        continue
                    if cls.get_status_from_resp(
                            resp) in cls.gw.ALLOWED_STATUTES:
                        trx.outer_update(
                            session, status=TransactionStatus.REPORTED.value)
                        cls.counter += 1
            logger.info(f'{cls.__name__} sent {cls.counter} '
                        f'transactions')


__TRANSACTIONS_TASKS__ = [CheckPlatformWalletsMonitor,
                          CheckTransactionsMonitor]
