from wallets.rpc import wallets_grpc
from wallets.gateway import method_classes


class WalletsService(wallets_grpc.WalletsBase):

    async def Healthz(self, stream):
        request = await stream.recv_message()
        await stream.send_message(
            await method_classes.HeathzMethod.process(request)
        )

    async def StartMonitoring(self, stream):
        request = await stream.recv_message()
        await stream.send_message(
            await method_classes.StartMonitoringMethod.process(request)
        )

    async def StopMonitoring(self, stream):
        request = await stream.recv_message()
        await stream.send_message(
            await method_classes.StopMonitoringMethod.process(request)
        )

    async def CheckBalance(self, stream):
        request = await stream.recv_message()
        await stream.send_message(
            await method_classes.CheckBalanceMethod.process(request)
        )

    async def UpdateTrx(self, stream):
        request = await stream.recv_message()
        await stream.send_message(
            await method_classes.UpdateTrxMethod.process(request)
        )

    async def GetInputTransactions(self, stream):
        request = await stream.recv_message()
        await stream.send_message(
            await method_classes.GetInputTrxMethod.process(request)
        )

    async def StartMonitoringPlatformWallet(self, stream):
        request = await stream.recv_message()
        await stream.send_message(
            await method_classes.StartMonitoringPlatformWLTMethod.process(
                request,
            )
        )

    async def AddInputTransaction(self, stream):
        request = await stream.recv_message()
        await stream.send_message(
            await method_classes.AddInputTransactionMethod.process(request)
        )
