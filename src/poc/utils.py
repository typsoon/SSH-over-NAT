# register_and_punch.py
import socket
import subprocess
import sys
import time

from ..client.kcptun_utils import run_kcptun_client, run_kcptun_server

LOCALHOST = "127.0.0.1"


def register_and_get_peer_name_and_addr(myname, sock, server_addr):
    # zarejestruj się u rendezvous
    sock.sendto(myname.encode(), server_addr)

    print(
        "Sent registration to",
        server_addr,
        # "from local udp port",
        # local_udp_port,
    )

    try:
        data, addr = sock.recvfrom(1024)
    except socket.timeout:
        print("No reply from rendezvous")
        sys.exit(2)

    reply = data.decode().strip().split()
    peername, peer_ip, peer_port = reply[0], reply[1], int(reply[2])
    print("Got peer:", peername, peer_ip, peer_port)

    peer_addr = (peer_ip, peer_port)

    return peername, peer_addr


def run_ssh_command(user, client_kcptun_port_listen):
    cmd = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        # "-o",
        # f"HostName={host}",
        "-p",
        str(client_kcptun_port_listen),
        f"{user}@{LOCALHOST}",
        # f"{'piotrek'}@{peer_addr[0]}",
    ]

    print(cmd)
    time.sleep(1)
    subprocess.run(cmd)


def run_client(myname, server_addr, local_udp_port, automatic_ssh):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(
            ("", local_udp_port)
        )  # ważne: wiążemy lokalny UDP port, który będzie źródłowym mappingiem
        sock.settimeout(10)

        peer_name, peer_addr = register_and_get_peer_name_and_addr(
            myname, sock, server_addr
        )

        print("Peer:", peer_name, peer_addr)

        with run_kcptun_client(peer_addr, local_kcptun_port=local_udp_port):
            print("KCPTUN was run")

            if automatic_ssh:
                run_ssh_command(peer_name, local_udp_port)


def run_server(myname, server_addr, listening_port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        bind_addr = ("", listening_port)
        sock.bind(
            bind_addr
        )  # ważne: wiążemy lokalny UDP port, który będzie źródłowym mappingiem
        sock.settimeout(10)

        peer_name, peer_addr = register_and_get_peer_name_and_addr(
            myname, sock, server_addr
        )

        print("Peer:", peer_name, peer_addr)

        sock.close()

        with run_kcptun_server(listening_port=listening_port):
            pass


# program zostaje uruchomiony w tle — możesz ctrl+c żeby przerwać
