from enum import Enum
from .config_manager import GlobalConfig
from .cache_dir import get_app_cache_dir


class DefaultKeys(Enum):
    server_ip = "default remote server ip"
    server_port = "default remote server port"
    local_server_port = "default local server port"
    local_client_port = "default local client port"


LOCALHOST = "127.0.0.1"
PHP_RENDEZVOUS_URL_FMSTR = "http://%s/hashed.php"
RELAY_URL_FMSTR = "http://%s/relay.php"

SSH_PORT = 22
APP_NAME = "ssh-over-nat"

config = GlobalConfig(
    DefaultKeys,
    APP_NAME,
    set_at_start={
        DefaultKeys.local_server_port.name: 8022,
        DefaultKeys.local_client_port.name: 8025,
    },
)
