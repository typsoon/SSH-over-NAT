import os
import getpass
from pathlib import Path
from dotenv import load_dotenv

from src.poc.utils import run_client, run_server

load_dotenv()
remote_ipaddr = os.getenv("REMOTE_SERVER_IP")
remote_udp_port = int(os.getenv("REMOTE_UDP_PORT", 50))  # Cast to Int!

server_addr = (remote_ipaddr, remote_udp_port)

poc_server_port = 8025
poc_client_listen_port = 8022

DOIT_CONFIG = {
    "verbosity": 2,
    "default_tasks": [],  # Optional: Prevent running everything by default
}


def task_poc_client():
    """Run the client-side NAT traversal."""
    myname = "__cli"

    def run_client_wrapper(no_automatic_ssh):
        # Invert the flag because run_client expects 'automatic_ssh' (True/False)
        automatic_ssh = not no_automatic_ssh

        print(f"DEBUG: Running client with automatic_ssh={automatic_ssh}")

        run_client(
            myname,
            server_addr,
            poc_client_listen_port,
            automatic_ssh,
        )

    return {
        "actions": [(run_client_wrapper,)],
        "params": [
            {
                "name": "no_automatic_ssh",
                "long": "no-automatic-ssh",  # The flag name: --no-automatic-ssh
                "type": bool,  # It's a boolean flag
                "default": False,  # Default is False (so SSH happens)
                "help": "Disable automatic SSH connection after NAT traversal",
            }
        ],
        # 'uptodate': [False] ensures the task always runs even if nothing changed
        "uptodate": [False],
    }


def task_poc_server():
    # print(myname)
    """Run the server-side NAT traversal."""
    myname = getpass.getuser()
    return {
        "actions": [(run_server, [myname, server_addr, poc_server_port])],
        "uptodate": [False],
    }
