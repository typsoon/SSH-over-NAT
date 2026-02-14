import argparse
from .utils import run_client, run_server

client_kcptun_port_listen = 8022

parser = argparse.ArgumentParser(
    description="UDP NAT traversal PoC: register with rendezvous and punch through NAT."
)
parser.add_argument("myname", help="Your name/identifier")
parser.add_argument("vps_ip", help="VPS IP address")
parser.add_argument("vps_port", type=int, help="VPS UDP port")
parser.add_argument("local_udp_port", type=int, help="Local UDP port to bind")
parser.add_argument(
    "role",
    choices=["server", "client"],
    help='Role: "server" or "client"',
)
parser.add_argument("--no-automatic-ssh", action="store_true")

if __name__ == "__main__":
    args = parser.parse_args()

    myname = args.myname
    vps_ip = args.vps_ip
    vps_port = args.vps_port
    local_udp_port = args.local_udp_port
    server_or_client = args.role

    server_addr = (vps_ip, vps_port)

    is_client: bool
    if server_or_client == "client":
        run_client(
            myname,
            server_addr,
            local_udp_port,
            client_kcptun_port_listen,
            not args.no_automatic_ssh,
        )
    elif server_or_client == "server":
        run_server(myname, server_addr, local_udp_port)
    else:
        raise Exception(f"Illegal argument {server_or_client}")
