import time
import schedule
from wallets import db
from wallets import conf
from wallets.monitoring import common
from wallets.utils import threaded


@threaded
def check_wallets():
    common.CheckWalletMonitor.process(db.session)


@threaded
def check_transactions():
    common.CheckTransactionsMonitor.process(db.session)


@threaded
def check_exchange_transactions():
    common.CheckPlatformWalletsMonitor.process(db.session)


@threaded
def send_to_transactions_service():
    common.SendToTransactionService.process(db.session)


@threaded
def send_to_exchanger_service():
    common.SendToExchangerService.process(db.session)


__tasks__ = [check_transactions, check_exchange_transactions,
             send_to_transactions_service, send_to_exchanger_service]

schedule.every(conf['MONITORING_WALLETS_PERIOD']).hours.do(
    check_wallets)

for func in __tasks__:
    schedule.every(conf['MONITORING_TRANSACTIONS_PERIOD']).minutes.do(func)


def run():
    while True:
        schedule.run_pending()
        time.sleep(1)
