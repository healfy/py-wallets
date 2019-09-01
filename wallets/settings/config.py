import os
import typing
from ruamel import yaml


yaml = yaml.YAML(typ='unsafe')
CONFIG_FILE_NAME = 'config.yaml'
LOCAL_CONFIG_FILE_NAME = 'local_config.yaml'
CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
SEARCH_PATHS: typing.List[str] = [
    CURRENT_PATH,
    '/etc/wallets'
]
cp = CURRENT_PATH
for i in range(3):
    cp = os.path.dirname(cp)
    SEARCH_PATHS.append(cp)

conf: dict = {'MAIL_PASSWORD': os.environ.get('MAILGUN_ACCESS_KEY')}
file_path = None
print(f'Searching configs in {SEARCH_PATHS}')
for p in SEARCH_PATHS:
    file_path = os.path.join(p, CONFIG_FILE_NAME)
    if os.path.exists(file_path):
        print(f'Loading config from {file_path}')
        with open(file_path) as f:
            conf.update(yaml.load(f))
local_conf_path = os.path.join(CURRENT_PATH, LOCAL_CONFIG_FILE_NAME)
if os.path.exists(local_conf_path):
    print(f'Loading local config from {local_conf_path}')
    with open(local_conf_path) as f:
        conf.update(yaml.load(f))
