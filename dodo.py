import os
import getpass
from pathlib import Path
from dotenv import load_dotenv

from src.poc.utils import run_client, run_server

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


def task_poc_client():
    """Run the client-side NAT traversal."""

    # 1. Wrapper to handle all the params
    def run_client_wrapper(
        myname, server_ip, server_port, local_udp_port, no_automatic_ssh
    ):
        automatic_ssh = not no_automatic_ssh
        server_addr = (server_ip, server_port)

        print(
            f"DEBUG: Connecting as '{myname}' to {server_addr} | Listen Port: {local_udp_port}"
        )

        run_client(
            myname,
            server_addr,
            local_udp_port,
            automatic_ssh,
        )

    return {
        "actions": [(run_client_wrapper,)],
        "params": [
            {
                "name": "myname",
                "long": "name",
                "short": "n",
                "type": str,
                "default": "__cli",
                "help": "Client identifier/nickname",
            },
            {
                "name": "server_ip",
                "long": "server-ip",
                "short": "ip",
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
                "help": "Remote VPS UDP port",
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
                "name": "no_automatic_ssh",
                "long": "no-automatic-ssh",
                "type": bool,
                "default": False,
                "help": "Disable automatic SSH connection",
            },
        ],
        "uptodate": [False],
    }


def task_poc_server():
    """Run the server-side NAT traversal."""

    # 1. Wrapper for server params
    def run_server_wrapper(myname, server_ip, server_port, local_udp_port):
        server_addr = (server_ip, server_port)

        print(
            f"DEBUG: Registering '{myname}' with {server_addr} | Local Bind: {local_udp_port}"
        )

        run_server(myname, server_addr, local_udp_port)

    return {
        "actions": [(run_server_wrapper,)],
        "params": [
            {
                "name": "myname",
                "long": "name",
                "short": "n",
                "type": str,
                "default": getpass.getuser(),
                "help": "Server identifier/nickname",
            },
            {
                "name": "server_ip",
                "long": "server-ip",
                "short": "srvip",
                "type": str,
                "default": DEFAULT_SERVER_IP,
                "help": "Server VPS IP address",
            },
            {
                "name": "server_port",
                "long": "server-port",
                "short": "srvp",
                "type": int,
                "default": DEFAULT_SERVER_PORT,
                "help": "Local UDP port to bind for NAT hole punching",
            },
            {
                "name": "local_udp_port",
                "long": "local-port",
                "short": "p",
                "type": int,
                "default": DEFAULT_LOCAL_PORT_FOR_SRV_MODE,
                "help": "Local port for KCPTun client to listen on",
            },
        ],
        "uptodate": [False],
    }
