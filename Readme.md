# Transactions Service

## Main responsibilities:

* **Wallets balance monitoring**
* **Report about input transactions**

## About project
* gRPC -- as the basis of the service
* grpclib -- for ascync server
* sqlalchemy flask-sqlalchemy  -- for database operation
* Postgresql -- as DB
* Pytest -- for tests
* Marchmallow -- to serialize and deserialize objects in protobuf/dict
* Ruamel -- to read yaml files that will config
* Rest-api grpc gateway for test via the REST
* Makefile for run some commands



## Run project

### Via venv on local machine
1. Clone repo
1. `cd to_project_root`
1. `./init_proto.bash` - for initialize proto files
1. Create virtualenv, example - `mkvirtualenv $(basename "$PWD") -p $(which python3.6)`
1. Install requirements - `pip install -r /req/requirements.txt.txt`
1. Start service `python wallets/server.py`

## Helpful commands
To run this commands you must have proto folder in project root.
In project root
* **make proto** - generate all *pb2, *pb2_grpc files needed to communication
 with services 
* **make wallets-gw** - generate Rest-api grpc gateway for test via the REST

## Run Tests

**You should know this:**
1. Directory with tests - `tests`.
2. Some useful parameters:
    * '--runslow' - running slow tests, for example: `pytest --runslow`

In root of project
+ all tests - execute `pytest -v tests` in root directory of project
+ all tests in some file? or example: `pytest tests/gateway/test_server.py`
+ single test in some file? for example: `pytest tests/gateway/test_server.py::TestWalletServer::test_healhtz_method`


## Run migrations
```bash
alembic current
alembic stamp head
alembic revision --autogenerate
alembic upgrade head
```
