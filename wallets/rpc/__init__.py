import sys
import os
sys.path.extend((os.path.abspath('..'), os.path.abspath('.'),  os.path.abspath('rpc'),))
from .blockchain_gateway_pb2_grpc import blockchain__gateway__pb2 as bc_gw
from .currencies_pb2_grpc import currencies__pb2 as currencies_pb2
