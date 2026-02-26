from ssh_over_nat.common import config, DefaultKeys as K
from ssh_over_nat.poc.utils import run_client, run_server, run_ssh_command

DOIT_CONFIG = {
    "verbosity": 2,
    "default_tasks": [],
}


def task_run_ssh_command():
    """SSH via tunnel"""

    def run_ssh_command_wrapper(username, local_udp_port):
        if username is None:
            print("Username ( -u ) is necessary to connect")
            return
            # raise TaskError(
            #     "Username ( -u ) is necessary to connect"
            # )
        run_ssh_command(username, local_udp_port)

    return {
        "actions": [(run_ssh_command_wrapper,)],
        "params": [
            {
                "name": "username",
                "long": "username",
                "short": "u",
                "type": str,
                "default": None,
                "help": "Username you want to log in to on the server machine",
            },
            {
                "name": "local_udp_port",
                "long": "local-port",
                "short": "p",
                "type": int,
                "default": config.get(K.local_client_port),
                "help": "Local tunnel entry port (the one KCPTun is listening on)",
            },
        ],
    }


def get_unset_str(name):
    return f"Default value for {name} not set. Run ssh_over_nat environment -a set -k {name} -v value"


def task_poc_client():
    """Run the client-side NAT traversal."""

    # 1. Wrapper to handle all the params
    def run_client_wrapper(hash, server_ip, server_port, local_udp_port, username):
        if hash is None:
            print("Hash ( -h ) is required")
            return
            # raise TaskError(
            #     "Hash ( -h ) is required"
            # )

        automatic_ssh = username is not None
        server_addr = (server_ip, server_port)

        for var, name in (
            [server_ip, K.server_ip.name],
            [server_port, K.server_port.name],
            [local_udp_port, K.local_client_port.name],
        ):
            if var is None:
                print(get_unset_str(name))
                return

        print(
            f"DEBUG: Querying '{hash}' at {server_addr} | Local Port: {local_udp_port}"
        )

        run_client(hash, server_addr, local_udp_port, automatic_ssh, username)

    return {
        "actions": [(run_client_wrapper,)],
        "params": [
            {
                "name": "hash",
                "long": "hash",
                "short": "h",
                "type": str,
                "default": None,
                "help": "Hash of the server you're trying to connect to [necessary]",
            },
            {
                "name": "server_ip",
                "long": "server-ip",
                "short": "i",
                "type": str,
                "default": config.get(K.server_ip),
                "help": "Remote VPS IP address",
            },
            {
                "name": "server_port",
                "long": "server-port",
                "short": "r",
                "type": int,
                "default": config.get(K.server_port),
                "help": "Remote VPS port",
            },
            {
                "name": "local_udp_port",
                "long": "local-port",
                "short": "p",
                "type": int,
                "default": config.get(K.local_client_port),
                "help": "Local port for KCPTun client to listen on",
            },
            {
                "name": "username",
                "long": "username",
                "short": "u",
                "type": str,
                "default": None,
                "help": "Login you want to connect to [required for automatic SSH]",
            },
        ],
        "uptodate": [False],
    }


def task_poc_server():
    """Run the server-side NAT traversal."""

    # 1. Wrapper for server params
    def run_server_wrapper(hash, server_ip, server_port, local_udp_port):
        if hash is None:
            print("Hash ( -h ) is required")
            return
            # raise TaskError(
            #     "Hash ( -h ) is required"
            # )

        server_addr = (server_ip, server_port)

        for var, name in (
            [server_ip, K.server_ip.name],
            [server_port, K.server_port.name],
            [local_udp_port, K.local_server_port.name],
        ):
            if var is None:
                print(get_unset_str(name))
                return

        print(
            f"DEBUG: Registering '{hash}' with {server_addr} | Local Bind: {local_udp_port}"
        )

        run_server(hash, server_addr, local_udp_port)

    return {
        "actions": [(run_server_wrapper,)],
        "params": [
            {
                "name": "hash",
                "long": "hash",
                "short": "h",
                "type": str,
                "default": None,
                "help": "Hash the server will be known as [necessary]",
            },
            {
                "name": "server_ip",
                "long": "server-ip",
                "short": "i",
                "type": str,
                "default": config.get(K.server_ip, None),
                "help": "Remote VPS IP address",
            },
            {
                "name": "server_port",
                "long": "server-port",
                "short": "r",
                "type": int,
                "default": config.get(K.server_port, None),
                "help": "Remote VPS port",
            },
            {
                "name": "local_udp_port",
                "long": "local-port",
                "short": "p",
                "type": int,
                "default": config.get(K.local_server_port, None),
                "help": "Port used by KCPTun server [not important]",
            },
        ],
        "uptodate": [False],
    }


environment_usage = "ssh_over_nat environment --action get|set --key key --value value"


def task_environment():
    """Get/set global environment config"""

    def set_value(key, value):
        if key not in map(lambda e: e.name, K):
            raise ValueError(f"Unknown key: {key}")

        default = config.get(key)
        if default is not None:
            value = type(default)(value)

        config.set(key, value)
        print(f"{key} = {value}")

    def get_value(key):
        if key == "all":
            for e in K:
                print(f"{e.name}={config.get(e.name, '')}")
            return

        if key not in map(lambda e: e.name, K):
            raise ValueError(f"Unknown key: {key}")

        if key:
            print(config.get(key, ""))

    def environment_action(action, key, value):
        if action is None:
            print(environment_usage)
            return

        if key is None:
            print("No key provided")
            return

        if action == "get":
            if value is not None:
                print("Too many args provided")
                return

            get_value(key)
        else:
            if value is None:
                print("No value provided")
                return

            set_value(key, value) if action == "set" else get_value(key)

    return {
        "actions": [(environment_action,)],
        "params": [
            {
                "name": "action",
                "long": "action",
                "short": "a",
                "choices": [("set", "set a value"), ("get", "retrieve a value")],
                "default": None,
            },
            {
                "name": "key",
                "long": "key",
                "short": "k",
                "choices": [(e.name, e.value) for e in K]
                + [("all", "print all values")],
                "default": None,
            },
            {
                "name": "value",
                "long": "value",
                "short": "v",
                "default": None,
            },
        ],
        "uptodate": [False],
    }
