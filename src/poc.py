# register_and_punch.py
import socket
import sys
import time
import threading
from client.kcptun_utils import run_client, run_server
import subprocess


def punch_loop():
    while True:
        try:
            sock.sendto(b"punch", (peer_ip, peer_port))
        except Exception as e:
            print("Punch send error:", e)
        time.sleep(1)


if len(sys.argv) != 6:
    print(
        'Usage: python3 register_and_punch.py <myname> <vps_ip> <vps_port> <local_udp_port> <"server"|"client">'
    )
    sys.exit(1)

myname = sys.argv[1]
vps_ip = sys.argv[2]
vps_port = int(sys.argv[3])
local_udp_port = int(sys.argv[4])
server_or_client = sys.argv[5]

is_client: bool
if server_or_client == "client":
    is_client = True
elif server_or_client == "server":
    is_client = False
else:
    raise Exception(f"Illegal argument {server_or_client}")


with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.bind(
        ("", local_udp_port)
    )  # ważne: wiążemy lokalny UDP port, który będzie źródłowym mappingiem
    sock.settimeout(10)

    # zarejestruj się u rendezvous
    sock.sendto(myname.encode(), (vps_ip, vps_port))
    print(
        "Sent registration to", vps_ip, vps_port, "from local udp port", local_udp_port
    )

    try:
        data, addr = sock.recvfrom(1024)
    except socket.timeout:
        print("No reply from rendezvous")
        sys.exit(2)

    reply = data.decode().strip().split()
    peername, peer_ip, peer_port = reply[0], reply[1], int(reply[2])
    print("Got peer:", peername, peer_ip, peer_port)

    # server_kcptun_port_listen = 8008
    client_kcptun_port_listen = 8022
    peer_addr = (peer_ip, peer_port)
    # peer_addr = (peer_ip, server_kcptun_port_listen)

    def thread_work():
        run_client(peer_addr, local_kcptun_port=client_kcptun_port_listen)

    if is_client:
        # thread_work()
        threading.Thread(target=thread_work).start()
        localhost = "127.0.0.1"

        print("KCPTUN was run")
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
            f"{'piotrek'}@{localhost}",
            # f"{'piotrek'}@{peer_addr[0]}",
        ]
        print(cmd)
        time.sleep(1)
        subprocess.run(cmd)
        print("IT was run")
    else:
        sock.close()
        run_server(listening_port=local_udp_port)

    # funkcja pingująca peer co 1s, aby utrzymać NAT mapping

    t = threading.Thread(target=punch_loop, daemon=True)
    # t.start()

    print(
        "Punching in background. Keep this running. Local UDP bound to", local_udp_port
    )
    print("Peer:", peer_ip, peer_port)
    # program zostaje uruchomiony w tle — możesz ctrl+c żeby przerwać
    while True:
        time.sleep(3600)
