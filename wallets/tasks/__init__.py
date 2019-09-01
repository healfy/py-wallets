import time
import schedule
from wallets.utils import threaded


@threaded
def print1():
    print('123123123')

@threaded
def print2():
    print('abraabar')

@threaded
def print3():
    print('werded')



schedule.every(10).seconds.do(print3)
schedule.every(10).seconds.do(print2)
schedule.every(10).seconds.do(print1)

while True:
    schedule.run_pending()
    time.sleep(1)
