SERVICE=wallets
PY_DIR=wallets

BC_PROTO = blockchain-gateway/proto
BC_PROTO_F = blockchain-gateway/proto/blockchain_gateway.proto

TRX_PROTO = transactions/proto
TRX_PROTO_F =  transactions/proto/transactions.proto

PROTO_PATH=proto/wallets.proto
PROTOC_INCLUDE = \
	-I=/usr/local/include \
	-I proto/ \
	-I $(BC_PROTO) \
	-I $(TRX_PROTO) \
	-I${GOPATH}/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
	-I${GOPATH}/src/github.com/grpc-ecosystem/grpc-gateway

PROTOC = python3 -m grpc.tools.protoc

# BUILD_FLAGS=-gcflags=all='-N -l' -ldflags="-linkmode=internal" -ldflags '-s' -buildmode=plugin

all: build


.PHONY: proto
proto: OUT_DIR=$(PY_DIR)/rpc

proto: $(PROTO_PATH)
	mkdir -p $(OUT_DIR)
	$(PROTOC) $(PROTOC_INCLUDE) \
		--grpc_python_out=$(OUT_DIR) \
		--python_grpc_out=$(OUT_DIR) \
		--python_out=plugins=grpc:$(OUT_DIR) $(PROTO_PATH)
	sed -ie 's/protoc-gen-swagger/protoc_gen_swagger/g' $(OUT_DIR)/wallets_grpc.py

wallets-gw: $(PROTO_PATH) proto
	$(PROTOC) $(PROTOC_INCLUDE) \
		--grpc-gateway_out=logtostderr=true:grpc_gw/proto \
		--swagger_out=logtostderr=true:grpc_gw $(PROTO_PATH)
	protoc $(PROTOC_INCLUDE) --go_out=plugins=grpc:grpc_gw/proto $(PROTO_PATH)  # for GOLANG client


bgw-proto:
	$(PROTOC) $(PROTOC_INCLUDE) $(BC_PROTO_F) --grpc_python_out=$(PY_DIR)/rpc --python_out=grpc:$(PY_DIR)/rpc

transactions-proto:
	$(PROTOC) $(PROTOC_INCLUDE) $(TRX_PROTO_F) --grpc_python_out=$(PY_DIR)/rpc --python_out=grpc:$(PY_DIR)/rpc
