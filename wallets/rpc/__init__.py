import sys
import os

sys.path.extend((os.path.abspath('..'), os.path.abspath('../..'), os.path.abspath('.'),  os.path.abspath('rpc'),))

from wallets.rpc.wallets_pb2_grpc import wallets__pb2 as wallets_pb2

from wallets.rpc.blockchain_gateway_pb2_grpc import blockchain__gateway__pb2 \
    as \
    blockchain_gateway_pb2

from wallets.rpc.currencies_pb2_grpc import currencies__pb2 as currencies_pb2

from wallets.rpc.transactions_pb2_grpc import transactions__pb2 as transactions_pb2

from wallets.rpc.exchanger_pb2_grpc import exchanger__pb2 as exchanger_pb2
