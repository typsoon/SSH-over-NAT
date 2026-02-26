from enum import Enum
from .config_manager import GlobalConfig


class DefaultKeys(Enum):
    server_ip = "default remote server ip"
    server_port = "default remote server port"
    local_server_port = "default local server port"
    local_client_port = "default local client port"


LOCALHOST = "127.0.0.1"
PHP_RENDEZVOUS_URL_FMSTR = "http://%s/hashed.php"
RELAY_URL_FMSTR = "http://%s/relay.php"

SSH_PORT = 22

# Global Defaults (Fallback if not provided via CLI)
DEFAULTS = {
    DefaultKeys.server_ip: None,
    DefaultKeys.server_port: None,
    DefaultKeys.local_server_port: 8025,
    DefaultKeys.local_client_port: 8022,
}

config = GlobalConfig(
    DefaultKeys,
    set_at_start={
        DefaultKeys.local_server_port.name: 8022,
        DefaultKeys.local_client_port.name: 8025,
    },
)
