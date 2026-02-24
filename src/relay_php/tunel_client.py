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
    
    # Próbujemy do skutku, ale z przerwami, żeby nie zabić serwera
    while True:
        try:
            res = session_tx.post(url, data=b64_data, timeout=5)
            if res.status_code == 200 and "OK" in res.text:
                return
        except:
            pass
        time.sleep(0.5)

def send_to_relay_buffered(channel, data):
    # Dzielimy na max 4KB, jeśli paczka jest gigantyczna
    CHUNK_SIZE = 4096
    for i in range(0, len(data), CHUNK_SIZE):
        send_chunk(channel, data[i:i+CHUNK_SIZE])

def recv_from_relay(channel):
    try:
        res = session_rx.get(f"{RELAY_URL}?action=recv&channel={channel}", timeout=5)
        if res.status_code == 200 and "[[[" in res.text:
            raw = res.text.split('[[[')[1].split(']]]')[0]
            decoded = base64.b64decode(raw)
            return decoded
    except:
        time.sleep(0.1)
    return b""

def local_to_http(sock):
    sock.settimeout(0.05) # Bardzo krótki timeout do zbierania danych
    while True:
        try:
            # --- BUFOROWANIE ---
            # Zbieramy dane przez max 50ms albo do uzbierania 4KB
            buffer = []
            total_len = 0
            start_time = time.time()
            
            while time.time() - start_time < 0.05 and total_len < 4096:
                try:
                    chunk = sock.recv(4096)
                    if not chunk: 
                        # Socket zamknięty
                        return 
                    buffer.append(chunk)
                    total_len += len(chunk)
                except socket.timeout:
                    # Brak więcej danych w tej chwili, wychodzimy z pętli zbierania
                    break
                except Exception:
                    return

            if buffer:
                # Sklejamy kawałki w jedną całość i wysyłamy RAZ
                full_data = b"".join(buffer)
                send_to_relay_buffered('c2s', full_data)
            
        except Exception:
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
            time.sleep(0.05)

def start_client():
    global tx_seq
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Nagle off, my robimy własny buforing
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1) 
    server.bind(('127.0.0.1', LISTEN_PORT))
    server.listen(1)
    
    print(f"[*] Cebula-Relay Klient (BUFFERED) gotowy!")
    
    while True:
        sock, addr = server.accept()
        print(f"\n[+] Połączono: {addr}")
        
        try: 
            session_tx.get(f"{RELAY_URL}?action=reset", timeout=4)
            time.sleep(0.5)
        except: pass
        
        tx_seq = 0
        send_to_relay_buffered('c2s', b"---NEW_SSH_SESSION---")
        
        t1 = threading.Thread(target=local_to_http, args=(sock,), daemon=True)
        t2 = threading.Thread(target=http_to_local, args=(sock,), daemon=True)
        t1.start()
        t2.start()

if __name__ == "__main__":
    start_client()