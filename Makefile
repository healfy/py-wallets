REGISTRY_BASE_URL=gcr.io
SERVICE=wallets
CURRENT_CONTEXT=`kubectl config current-context`
BASE_IMAGE=$(SERVICE)-base
PY_DIR=wallets

BC_PROTO = blockchain-gateway/proto
BC_PROTO_F = blockchain-gateway/proto/blockchain_gateway.proto

PROTO_PATH=proto/wallets.proto
PROTOC_INCLUDE = \
	-I=/usr/local/include \
	-I proto/ \
	-I $(BC_PROTO) \
	-I${GOPATH}/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
	-I${GOPATH}/src/github.com/grpc-ecosystem/grpc-gateway

PROTOC = python3 -m grpc.tools.protoc

PROD ?= 0
STAGE ?= 0
ifeq ($(PROD), 1)
	ENV=prod
	PROJECT=bonum-prod
	IMAGE_TAG=stable
	CONTEXT=gke_bonum-prod_us-central1_main-cluster
else ifeq ($(STAGE), 1)
	ENV=stage
	PROJECT=api-project-206881048866
	IMAGE_TAG=stage
	CONTEXT=gke_api-project-206881048866_us-central1-a_ico
else
	ENV=dev
	PROJECT=api-project-206881048866
	IMAGE_TAG=dev
	CONTEXT=gke_api-project-206881048866_us-central1-a_ico
endif

DEPLOYMENT_FILE=deployment-$(ENV).yaml
DOCKERFILE=Dockerfile-$(ENV)
DOCKER_BASE_FILE=Dockerfile-base-$(ENV)

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


build-base: IMAGE_URL=$(REGISTRY_BASE_URL)/$(PROJECT)/$(BASE_IMAGE):$(IMAGE_TAG)
build-base: DOCKERFILE=$(DOCKER_BASE_FILE)
build-base: _build req/*.txt

build-base-gw: IMAGE_URL=$(REGISTRY_BASE_URL)/$(PROJECT)/$(SERVICE)-gw-base:$(IMAGE_TAG)
build-base-gw: DOCKERFILE=Dockerfile-gw-base
build-base-gw: _build grpc_gw/*

build-gw: IMAGE_URL=$(REGISTRY_BASE_URL)/$(PROJECT)/$(SERVICE)-gw:$(IMAGE_TAG)
build-gw: DOCKERFILE=Dockerfile-gw
build-gw: _build grpc_gw/* build-base-gw


build: IMAGE_URL=$(REGISTRY_BASE_URL)/$(PROJECT)/$(SERVICE):$(IMAGE_TAG)
build: proto _build

_build:
	docker build . -t $(IMAGE_URL) -f $(DOCKERFILE)
	gcloud docker -- push $(IMAGE_URL)


deploy: DEPLOYMENT_FILE_TMP=/tmp/$(SERVICE)-$(DEPLOYMENT_FILE)
deploy: build
	sed -re "s=COMMIT_HASH=`git rev-parse HEAD`=" $(DEPLOYMENT_FILE) > $(DEPLOYMENT_FILE_TMP)
	echo "*** DEPLOYING ***"
	kubectl config use-context $(CONTEXT)
	kubectl apply -f $(DEPLOYMENT_FILE_TMP)
	kubectl config use-context $(CURRENT_CONTEXT)
	rm -rf $(DEPLOYMENT_FILE_TMP)
