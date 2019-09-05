import time
import schedule
from wallets import conf
from wallets.monitoring import common
from wallets.utils import threaded


@threaded
def check_wallets():
    common.CheckWalletMonitor.process()


@threaded
def check_transactions():
    common.CheckTransactionsMonitor.process()


schedule.every(conf['MONITORING_WALLETS_PERIOD']).hours.do(
    check_wallets)
schedule.every(conf['MONITORING_TRANSACTIONS_PERIOD']).minutes.do(
    check_transactions)


while True:
    schedule.run_pending()
    time.sleep(1)
