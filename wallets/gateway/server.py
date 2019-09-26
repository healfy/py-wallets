from wallets.rpc import wallets_grpc
from wallets.gateway import method_classes
from wallets import db


class WalletsService(wallets_grpc.WalletsBase):

    async def Healthz(self, stream):
        request = await stream.recv_message()
        await stream.send_message(method_classes.HeathzMethod.process(
            request, db.session
        ))

    async def StartMonitoring(self, stream):
        request = await stream.recv_message()
        await stream.send_message(method_classes.StartMonitoringMethod.process(
            request, db.session
        ))

    async def StopMonitoring(self, stream):
        request = await stream.recv_message()
        await stream.send_message(method_classes.StopMonitoringMethod.process(
            request, db.session
        ))

    async def CheckBalance(self, stream):
        request = await stream.recv_message()
        await stream.send_message(method_classes.CheckBalanceMethod.process(
            request, db.session
        ))

    async def UpdateTrx(self, stream):
        request = await stream.recv_message()
        await stream.send_message(method_classes.UpdateTrxMethod.process(
            request, db.session
        ))

    async def GetInputTransactions(self, stream):
        request = await stream.recv_message()
        await stream.send_message(method_classes.GetInputTrxMethod.process(
            request, db.session
        ))
