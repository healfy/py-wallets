from wallets.rpc import wallets_grpc
from wallets.rpc.wallets_pb2_grpc import wallets__pb2 as w_pb2


class WalletsService(wallets_grpc.WalletsBase):

    async def Healthz(self, stream):
        request = await stream.recv_message()
        print("Healthchecking")
        await stream.send_message(w_pb2.HealthzResponse(

        ))

    async def GetWallet(self, stream):
        pass

    async def StartMonitoring(self, stream):
        pass

    async def StopMonitoring(self, stream):
        pass
