import os
import abc
import typing

from decimal import Decimal
from decimal import ROUND_HALF_UP
from datetime import datetime
from datetime import timedelta
from aioredlock import Aioredlock
from wallets.utils.consts import TransactionStatus

from wallets import (
    app,
    logger,
    objects,
    MyManager
)

from wallets.common import (
    Wallet,
    Transaction
)
from wallets.utils import (
    send_message,
    nested_commit_on_success
)

from wallets.gateway.base import (
    BaseGateway,
    BaseAsyncGateway
)

from wallets.gateway import (
    exchanger_service_gw,
    transactions_service_gw,
    blockchain_service_gw as b_gw,
    currencies_service_gw as c_gw,
)


conf = app.config

REDIS_HOST = os.environ.get('REDIS_HOST', conf.get('REDIS_HOST'))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')

lock_manager = Aioredlock(
    dict(host=REDIS_HOST, password=REDIS_PASSWORD), lock_timeout=120
)


class BaseMonitorClass(abc.ABC):
    """
    Base class for monitoring
    """
    timeout: int = conf['MONITORING_TRANSACTIONS_PERIOD']
    counter: int = 0  # for logging
    manager: MyManager = objects

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
    manager: MyManager

    @classmethod
    async def save(
            cls,
            wallet: Wallet,
            request_object: typing.Dict,
    ) -> typing.NoReturn:

        trx = await cls.manager.create(Transaction, **request_object)
        trx.wallet_id = wallet.id
        await cls.manager.update(trx)


class UpdateTrx:
    """
    Class for update transaction if it necessary
    """

    manager: MyManager
    counter: int

    @classmethod
    async def update(
            cls,
            wallet: typing.Type['Wallet'],
            trx: typing.Dict,
    ) -> typing.NoReturn:
        try:
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
            await cls.manager.update(trx)
            cls.counter += 1
        except Transaction.DoesNotExist:
            pass


class ValidateTRX:
    """
    Class to check transaction in base
    """
    manager: MyManager

    @classmethod
    def is_input_trx(
            cls,
            address: str,
            wallet: Wallet
    ) -> bool:
        return wallet.address.lower() == address.lower()

    @classmethod
    async def is_valid(cls, trx: dict, wallet: Wallet) -> bool:
        return (
                not await cls.manager.exists(Transaction, hash=trx['hash'])
                and cls.is_input_trx(trx['address_to'], wallet)
        )


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
    async def get_data(cls) -> typing.Optional[list]:
        return await cls.manager.get_all(Wallet,
                                         on_monitoring=True,
                                         is_platform=False,
                                         is_active=True)

    @classmethod
    async def _execute(
            cls,
    ) -> typing.NoReturn:

        for wallet in await cls.get_data():
            key = Wallet.lock_name_by_id(wallet.id)

            if not await lock_manager.is_locked(key):
                async with await lock_manager.lock(key) as lock:
                    assert lock.valid

                    trx_list = await b_gw.get_transactions_list(
                        wallet_address=wallet.address,
                        external_id=wallet.external_id
                    )
                    for trx in trx_list:
                        if await cls.is_valid(trx, wallet):
                            await cls.save(wallet, trx)
                            cls.counter += 1

                assert lock.valid is False

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
    async def get_data(cls) -> typing.Optional[list]:
        return await cls.manager.get_all(Wallet,
                                         on_monitoring=True,
                                         is_platform=True,
                                         is_active=True)

    @classmethod
    async def _execute(
            cls,
    ) -> typing.NoReturn:

        for wallet in await cls.get_data():
            key = Wallet.lock_name_by_id(wallet.id)

            if not await lock_manager.is_locked(key):
                async with await lock_manager.lock(key) as lock:
                    assert lock.valid

                    trx_list = await b_gw.get_exchanger_wallet_trx_list(
                        slug=wallet.currency_slug,
                        from_time=datetime.now() - timedelta(
                            days=cls.time_delta_days)
                    )
                    for trx in trx_list:
                        if await cls.is_valid(trx, wallet):
                            await cls.update(wallet, trx)
                assert lock.valid is False

        logger.info(f'{cls.__name__} updated {cls.counter} '
                    f'transactions')


class SendTrxToExternalService(BaseMonitorClass, abc.ABC):
    status: TransactionStatus
    gw: typing.Union[
        typing.Type['BaseGateway'], typing.Type['BaseAsyncGateway']
    ]
    func = typing.Awaitable[typing.Callable]

    @classmethod
    def get_status_from_resp(cls, response: dict):
        return cls.gw.MODULE.ResponseStatus.Value(
            response[cls.gw.response_attr]['status'])

    @classmethod
    async def set_status(cls, resp: dict, trx: Transaction):
        if cls.get_status_from_resp(resp) in cls.gw.ALLOWED_STATUTES:
            trx.status = cls.status
            trx.save()
            cls.counter += 1

    @classmethod
    async def _execute(
            cls,
    ) -> typing.NoReturn:

        for trx in await cls.get_data():
            key = Transaction.lock_name_by_id(trx.id)

            if not await lock_manager.is_locked(key):
                async with await lock_manager.lock(key) as lock:
                    assert lock.valid

                    try:
                        resp = await cls.func([trx])
                    except cls.gw.EXC_CLASS as exc:
                        logger.error(f'{cls.__name__} got exc from '
                                     f'TransactionService {exc}')
                        continue

                    await cls.set_status(resp, trx)
                assert lock.valid is False

            logger.info(f'{cls.__name__} sent {cls.counter} '
                        f'transactions')


class SendToTransactionService(SendTrxToExternalService):
    """
    Put all transactions to the external service "Transactions".
    Where they will monitor and also are sent back
    """
    gw = transactions_service_gw
    status = TransactionStatus.SENT.value
    func = transactions_service_gw.put_on_monitoring

    @classmethod
    async def get_data(cls) -> typing.Optional[list]:

        return await cls.manager.get_all(
            Transaction,
            Transaction.hash != None,
            Transaction.status == TransactionStatus.NEW.value,
        )


class SendToExchangerService(SendTrxToExternalService):
    """
    Put all confirmed input transactions associated with platform wallets to
    the external service "Exchanger"
    """

    gw = exchanger_service_gw
    status = TransactionStatus.REPORTED.value
    func = exchanger_service_gw.update_transactions

    @classmethod
    async def get_data(cls) -> typing.Optional[list]:

        query = Transaction.select().join(Wallet).where(
            (Transaction.hash != None) &
            (Transaction.uuid != None) &
            (Wallet.is_platform == True) &
            (Transaction.status == TransactionStatus.CONFIRMED.value)
        )

        return await cls.manager.get_all(query)


__TRANSACTIONS_TASKS__ = [
    SendToExchangerService,
    SendToTransactionService,
    CheckTransactionsMonitor,
   # CheckPlatformWalletsMonitor
]
