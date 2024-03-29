# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: wallets.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.const
import grpclib.client
if typing.TYPE_CHECKING:
    import grpclib.server

import google.protobuf.timestamp_pb2
import google.protobuf.duration_pb2
import google.api.annotations_pb2
import protoc_gen_swagger.options.annotations_pb2
import wallets_pb2


class WalletsBase(abc.ABC):

    @abc.abstractmethod
    async def Healthz(self, stream: 'grpclib.server.Stream[wallets_pb2.HealthzRequest, wallets_pb2.HealthzResponse]') -> None:
        pass

    @abc.abstractmethod
    async def StartMonitoring(self, stream: 'grpclib.server.Stream[wallets_pb2.MonitoringRequest, wallets_pb2.MonitoringResponse]') -> None:
        pass

    @abc.abstractmethod
    async def StopMonitoring(self, stream: 'grpclib.server.Stream[wallets_pb2.MonitoringRequest, wallets_pb2.MonitoringResponse]') -> None:
        pass

    @abc.abstractmethod
    async def CheckBalance(self, stream: 'grpclib.server.Stream[wallets_pb2.CheckBalanceRequest, wallets_pb2.CheckBalanceResponse]') -> None:
        pass

    @abc.abstractmethod
    async def UpdateTrx(self, stream: 'grpclib.server.Stream[wallets_pb2.TransactionRequest, wallets_pb2.TransactionResponse]') -> None:
        pass

    @abc.abstractmethod
    async def GetInputTransactions(self, stream: 'grpclib.server.Stream[wallets_pb2.InputTransactionsRequest, wallets_pb2.InputTransactionsResponse]') -> None:
        pass

    @abc.abstractmethod
    async def StartMonitoringPlatformWallet(self, stream: 'grpclib.server.Stream[wallets_pb2.PlatformWLTMonitoringRequest, wallets_pb2.PlatformWLTMonitoringResponse]') -> None:
        pass

    @abc.abstractmethod
    async def AddInputTransaction(self, stream: 'grpclib.server.Stream[wallets_pb2.InputTransactionRequest, wallets_pb2.InputTransactionResponse]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/wallets.Wallets/Healthz': grpclib.const.Handler(
                self.Healthz,
                grpclib.const.Cardinality.UNARY_UNARY,
                wallets_pb2.HealthzRequest,
                wallets_pb2.HealthzResponse,
            ),
            '/wallets.Wallets/StartMonitoring': grpclib.const.Handler(
                self.StartMonitoring,
                grpclib.const.Cardinality.UNARY_UNARY,
                wallets_pb2.MonitoringRequest,
                wallets_pb2.MonitoringResponse,
            ),
            '/wallets.Wallets/StopMonitoring': grpclib.const.Handler(
                self.StopMonitoring,
                grpclib.const.Cardinality.UNARY_UNARY,
                wallets_pb2.MonitoringRequest,
                wallets_pb2.MonitoringResponse,
            ),
            '/wallets.Wallets/CheckBalance': grpclib.const.Handler(
                self.CheckBalance,
                grpclib.const.Cardinality.UNARY_UNARY,
                wallets_pb2.CheckBalanceRequest,
                wallets_pb2.CheckBalanceResponse,
            ),
            '/wallets.Wallets/UpdateTrx': grpclib.const.Handler(
                self.UpdateTrx,
                grpclib.const.Cardinality.UNARY_UNARY,
                wallets_pb2.TransactionRequest,
                wallets_pb2.TransactionResponse,
            ),
            '/wallets.Wallets/GetInputTransactions': grpclib.const.Handler(
                self.GetInputTransactions,
                grpclib.const.Cardinality.UNARY_UNARY,
                wallets_pb2.InputTransactionsRequest,
                wallets_pb2.InputTransactionsResponse,
            ),
            '/wallets.Wallets/StartMonitoringPlatformWallet': grpclib.const.Handler(
                self.StartMonitoringPlatformWallet,
                grpclib.const.Cardinality.UNARY_UNARY,
                wallets_pb2.PlatformWLTMonitoringRequest,
                wallets_pb2.PlatformWLTMonitoringResponse,
            ),
            '/wallets.Wallets/AddInputTransaction': grpclib.const.Handler(
                self.AddInputTransaction,
                grpclib.const.Cardinality.UNARY_UNARY,
                wallets_pb2.InputTransactionRequest,
                wallets_pb2.InputTransactionResponse,
            ),
        }


class WalletsStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.Healthz = grpclib.client.UnaryUnaryMethod(
            channel,
            '/wallets.Wallets/Healthz',
            wallets_pb2.HealthzRequest,
            wallets_pb2.HealthzResponse,
        )
        self.StartMonitoring = grpclib.client.UnaryUnaryMethod(
            channel,
            '/wallets.Wallets/StartMonitoring',
            wallets_pb2.MonitoringRequest,
            wallets_pb2.MonitoringResponse,
        )
        self.StopMonitoring = grpclib.client.UnaryUnaryMethod(
            channel,
            '/wallets.Wallets/StopMonitoring',
            wallets_pb2.MonitoringRequest,
            wallets_pb2.MonitoringResponse,
        )
        self.CheckBalance = grpclib.client.UnaryUnaryMethod(
            channel,
            '/wallets.Wallets/CheckBalance',
            wallets_pb2.CheckBalanceRequest,
            wallets_pb2.CheckBalanceResponse,
        )
        self.UpdateTrx = grpclib.client.UnaryUnaryMethod(
            channel,
            '/wallets.Wallets/UpdateTrx',
            wallets_pb2.TransactionRequest,
            wallets_pb2.TransactionResponse,
        )
        self.GetInputTransactions = grpclib.client.UnaryUnaryMethod(
            channel,
            '/wallets.Wallets/GetInputTransactions',
            wallets_pb2.InputTransactionsRequest,
            wallets_pb2.InputTransactionsResponse,
        )
        self.StartMonitoringPlatformWallet = grpclib.client.UnaryUnaryMethod(
            channel,
            '/wallets.Wallets/StartMonitoringPlatformWallet',
            wallets_pb2.PlatformWLTMonitoringRequest,
            wallets_pb2.PlatformWLTMonitoringResponse,
        )
        self.AddInputTransaction = grpclib.client.UnaryUnaryMethod(
            channel,
            '/wallets.Wallets/AddInputTransaction',
            wallets_pb2.InputTransactionRequest,
            wallets_pb2.InputTransactionResponse,
        )
