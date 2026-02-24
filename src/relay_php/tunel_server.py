import socket
import threading
import time
import requests
import base64

RELAY_URL = "http://16.171.4.247/relay.php"
SSH_PORT = 22

session_tx = requests.Session()
session_rx = requests.Session()
current_sock = None
tx_seq = 0

def send_chunk(channel, data):
    global tx_seq
    tx_seq += 1
    local_seq = tx_seq
    b64_data = base64.b64encode(data).decode('utf-8')
    url = f"{RELAY_URL}?action=send&channel={channel}&seq={local_seq}"
    
    while True:
        try:
            res = session_tx.post(url, data=b64_data, timeout=4)
            if res.status_code == 200 and "OK" in res.text:
                time.sleep(0.01) # ODDECH
                return
        except:
            pass
        time.sleep(0.2)

def send_to_relay(channel, data):
    CHUNK_SIZE = 2048
    for i in range(0, len(data), CHUNK_SIZE):
        chunk = data[i:i+CHUNK_SIZE]
        send_chunk(channel, chunk)

def recv_from_relay(channel):
    try:
        res = session_rx.get(f"{RELAY_URL}?action=recv&channel={channel}", timeout=4)
        if res.status_code == 200 and "[[[" in res.text:
            raw = res.text.split('[[[')[1].split(']]]')[0]
            decoded = base64.b64decode(raw)
            return decoded
    except:
        time.sleep(0.1)
    return b""

def ssh_to_http(sock):
    while True:
        try:
            data = sock.recv(4096)
            if not data: break
            send_to_relay('s2c', data)
        except:
            break
    try: sock.close()
    except: pass

def main_loop():
    global current_sock, tx_seq
    print(f"[*] Cebula-Relay Serwer (STABLE) gotowy.")
    
    while True:
        data = recv_from_relay('c2s')
        if data:
            if b"---NEW_SSH_SESSION---" in data:
                print("\n[+] Nowa sesja.")
                tx_seq = 0
                if current_sock:
                    try: current_sock.close()
                    except: pass
                
                current_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                current_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                try:
                    current_sock.connect(('127.0.0.1', SSH_PORT))
                    threading.Thread(target=ssh_to_http, args=(current_sock,), daemon=True).start()
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
                    try: current_sock.sendall(data)
                    except: pass
        else:
            time.sleep(0.02) # Minimalny sleep zawsze

if __name__ == "__main__":
    main_loop()