import socket
import threading
import time
import requests
import base64

from ..common import (
    LOCALHOST,
    RELAY_URL_FMSTR,
)

# LISTEN_PORT = DEFAULT_LOCAL_PORT_FOR_CLIENT_MODE

session_tx = requests.Session()
session_rx = requests.Session()
tx_seq = 0
current_conn_id = 0


def send_chunk(channel, data, relay_url):
    global tx_seq
    tx_seq += 1
    local_seq = tx_seq

    b64_data = base64.b64encode(data).decode("utf-8")
    url = f"{relay_url}?action=send&channel={channel}&seq={local_seq}"

    while True:
        try:
            res = session_tx.post(url, data=b64_data, timeout=5)
            if res.status_code == 200 and "OK" in res.text:
                return
        except Exception:
            pass
        time.sleep(0.5)


def send_to_relay_buffered(channel, data, relay_url):
    CHUNK_SIZE = 4096
    for i in range(0, len(data), CHUNK_SIZE):
        send_chunk(channel, data[i : i + CHUNK_SIZE], relay_url)


def recv_from_relay(channel, relay_url):
    try:
        res = session_rx.get(f"{relay_url}?action=recv&channel={channel}", timeout=5)
        if res.status_code == 200 and "[[[" in res.text:
            raw = res.text.split("[[[")[1].split("]]]")[0]
            decoded = base64.b64decode(raw)
            return decoded
    except Exception:
        time.sleep(0.1)
    return b""


def local_to_http(sock, my_conn_id, relay_url):
    global current_conn_id
    sock.settimeout(0.05)

    while current_conn_id == my_conn_id:
        try:
            buffer = []
            total_len = 0
            start_time = time.time()

            while time.time() - start_time < 0.05 and total_len < 4096:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        return
                    buffer.append(chunk)
                    total_len += len(chunk)
                except socket.timeout:
                    break
                except Exception:
                    return

            if buffer:
                full_data = b"".join(buffer)
                send_to_relay_buffered("c2s", full_data, relay_url)

        except Exception:
            break


def http_to_local(sock, my_conn_id, relay_url):
    global current_conn_id

    while current_conn_id == my_conn_id:
        data = recv_from_relay("s2c", relay_url)
        if data:
            try:
                sock.sendall(data)
            except Exception:
                break
        else:
            time.sleep(0.05)
    print(f"[-] Stary wątek odbierający (ID: {my_conn_id}) został ubity.")


def start_client(server_port, listen_port):
    relay_url = RELAY_URL_FMSTR % server_port

    global tx_seq, current_conn_id
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    server.bind((LOCALHOST, listen_port))
    server.listen(1)

    print("[*] Cebula-Relay Klient (BUFFERED) gotowy!")

    while True:
        sock, addr = server.accept()
        print(f"\n[+] Połączono: {addr}")

        current_conn_id += 1
        my_conn_id = current_conn_id

        try:
            session_tx.get(f"{relay_url}?action=reset", timeout=4)
            time.sleep(0.5)
        except Exception as e:
            print(f"Exception {e}")

        tx_seq = 0
        send_to_relay_buffered("c2s", b"---NEW_SSH_SESSION---", relay_url)

        t1 = threading.Thread(
            target=local_to_http, args=(sock, my_conn_id), daemon=True
        )
        t2 = threading.Thread(
            target=http_to_local, args=(sock, my_conn_id), daemon=True
        )
        t1.start()
        t2.start()
