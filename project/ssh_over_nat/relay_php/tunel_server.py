import socket
import threading
import time
import requests
import base64

from ..common import LOCALHOST, RELAY_URL_FMSTR, SSH_PORT

session_tx = requests.Session()
session_rx = requests.Session()
current_sock = None
tx_seq = 0


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


def ssh_to_http(sock, relay_url):
    sock.settimeout(0.05)
    while True:
        try:
            # --- BUFOROWANIE ---
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
                send_to_relay_buffered("s2c", full_data, relay_url)

        except Exception:
            break
    try:
        sock.close()
    except Exception:
        pass


def main_loop(server_ip):
    global current_sock, tx_seq
    print("[*] Cebula-Relay Serwer (BUFFERED) gotowy.")

    relay_url = RELAY_URL_FMSTR % server_ip
    ttime = 0
    while True:
        data = recv_from_relay("c2s", relay_url)
        if data:
            ttime=0
            if b"---NEW_SSH_SESSION---" in data:
                print("\n[+] Nowa sesja.")
                tx_seq = 0
                if current_sock:
                    try:
                        current_sock.close()
                    except Exception:
                        pass

                current_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                current_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                try:
                    current_sock.connect((LOCALHOST, SSH_PORT))
                    threading.Thread(
                        target=ssh_to_http, args=(current_sock, relay_url), daemon=True
                    ).start()
                except Exception as e:
                    print(f"[!] Błąd SSH: {e}")
                    current_sock = None
                    continue

                parts = data.split(b"---NEW_SSH_SESSION---")
                new_data = parts[-1]
                if len(new_data) > 0 and current_sock:
                    current_sock.sendall(new_data)
            else:
                if current_sock:
                    try:
                        current_sock.sendall(data)
                    except Exception:
                        pass
        else:
            time.sleep(0.05)
            ttime += 0.05
            if(ttime > 150):
                return