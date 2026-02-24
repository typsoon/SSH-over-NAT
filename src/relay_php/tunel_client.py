import socket
import threading
import time
import requests
import base64

RELAY_URL = "http://16.171.4.247/relay.php"
LISTEN_PORT = 2222

session_tx = requests.Session()
session_rx = requests.Session()
tx_seq = 0 

def send_chunk(channel, data):
    global tx_seq
    tx_seq += 1
    local_seq = tx_seq
    
    b64_data = base64.b64encode(data).decode('utf-8')
    url = f"{RELAY_URL}?action=send&channel={channel}&seq={local_seq}"
    
    # Retry loop - próbujemy do skutku, ale z małym oddechem
    while True:
        try:
            res = session_tx.post(url, data=b64_data, timeout=4)
            if res.status_code == 200 and "OK" in res.text:
                time.sleep(0.01) # ODDECH DLA SERWERA
                return
        except:
            pass
        # Jak błąd, czekamy chwilę dłużej żeby sieć wstała
        time.sleep(0.2)

def send_to_relay(channel, data):
    # Dzielimy duże pakiety (np. wklejenie tekstu) na kawałki max 2KB
    # To zapobiega zapchaniu się PHP przy dużej ilości danych
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

def local_to_http(sock):
    while True:
        try:
            data = sock.recv(4096)
            if not data: break
            send_to_relay('c2s', data)
        except:
            break

def http_to_local(sock):
    while True:
        data = recv_from_relay('s2c')
        if data:
            try:
                sock.sendall(data)
            except:
                break
        else:
            # Ważne: Sleep nawet jak pusto, żeby nie palić CPU
            time.sleep(0.02) 

def start_client():
    global tx_seq
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    server.bind(('127.0.0.1', LISTEN_PORT))
    server.listen(1)
    
    print(f"[*] Cebula-Relay Klient (STABLE) gotowy!")
    
    while True:
        sock, addr = server.accept()
        print(f"\n[+] Połączono: {addr}")
        
        try: 
            session_tx.get(f"{RELAY_URL}?action=reset", timeout=3)
            time.sleep(0.5)
        except: pass
        
        tx_seq = 0
        send_to_relay('c2s', b"---NEW_SSH_SESSION---")
        
        t1 = threading.Thread(target=local_to_http, args=(sock,), daemon=True)
        t2 = threading.Thread(target=http_to_local, args=(sock,), daemon=True)
        t1.start()
        t2.start()

if __name__ == "__main__":
    start_client()