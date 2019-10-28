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


schedule.every(conf['MONITORING_WALLETS_PERIOD']).hours.do(
    check_wallets)
schedule.every(conf['MONITORING_TRANSACTIONS_PERIOD']).minutes.do(
    check_transactions)

schedule.every(conf['MONITORING_TRANSACTIONS_PERIOD']).minutes.do(
    check_exchange_transactions)


def run():
    while True:
        schedule.run_pending()
        time.sleep(1)
