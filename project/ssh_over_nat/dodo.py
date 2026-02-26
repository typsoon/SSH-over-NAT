import os
from dotenv import load_dotenv

from ssh_over_nat.poc.utils import run_client, run_server, run_ssh_command

load_dotenv()

# Global Defaults (Fallback if not provided via CLI)
DEFAULT_SERVER_IP = os.getenv("REMOTE_SERVER_IP", "127.0.0.1")
DEFAULT_SERVER_PORT = int(os.getenv("REMOTE_UDP_PORT", 50))
DEFAULT_LOCAL_PORT_FOR_SRV_MODE = 8025
DEFAULT_LOCAL_PORT_FOR_CLIENT_MODE = 8022

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
                "default": DEFAULT_LOCAL_PORT_FOR_CLIENT_MODE,
                "help": "Local tunnel entry port (the one KCPTun is listening on)",
            },
        ],
    }


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
                "short": "srvip",
                "type": str,
                "default": DEFAULT_SERVER_IP,
                "help": "Remote VPS IP address",
            },
            {
                "name": "server_port",
                "long": "server-port",
                "short": "srvprt",
                "type": int,
                "default": DEFAULT_SERVER_PORT,
                "help": "Remote VPS port",
            },
            {
                "name": "local_udp_port",
                "long": "local-port",
                "short": "p",
                "type": int,
                "default": DEFAULT_LOCAL_PORT_FOR_CLIENT_MODE,
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
                "short": "srvip",
                "type": str,
                "default": DEFAULT_SERVER_IP,
                "help": "Remote VPS IP address",
            },
            {
                "name": "server_port",
                "long": "server-port",
                "short": "srvprt",
                "type": int,
                "default": DEFAULT_SERVER_PORT,
                "help": "Remote VPS port",
            },
            {
                "name": "local_udp_port",
                "long": "local-port",
                "short": "p",
                "type": int,
                "default": DEFAULT_LOCAL_PORT_FOR_SRV_MODE,
                "help": "Port used by KCPTun server [not important]",
            },
        ],
        "uptodate": [False],
    }
