import socket
import threading
import time
import requests
import base64

RELAY_URL = "http://16.171.4.247/relay.php"  # <--- PODMIEŃ
LISTEN_PORT = 2222

session = requests.Session()

def send_to_relay(channel, data):
    # DEBUG PRINT
    print(f"[DEBUG WYSYŁAM -> {channel}] {len(data)} bajtów | Podgląd: {repr(data[:50])}")
    
    b64_data = base64.b64encode(data).decode('utf-8')
    while True:
        try:
            res = session.post(f"{RELAY_URL}?action=send&channel={channel}", data=b64_data, timeout=5)
            if res.status_code == 200 and "OK" in res.text:
                break
            else:
                print(f"[!] Błąd POST: {res.status_code} | {res.text[:30]}")
                time.sleep(1)
        except Exception as e:
            print(f"[!] Błąd sieci (wysyłanie): {e}")
            time.sleep(1)

def recv_from_relay(channel):
    try:
        res = session.get(f"{RELAY_URL}?action=recv&channel={channel}", timeout=5)
        if res.status_code == 200 and "[[[" in res.text and "]]]" in res.text:
            b64_data = res.text.split('[[[')[1].split(']]]')[0]
            decoded = base64.b64decode(b64_data)
            
            # DEBUG PRINT
            if len(decoded) > 0:
                print(f"[DEBUG ODBIERAM <- {channel}] {len(decoded)} bajtów | Podgląd: {repr(decoded[:50])}")
                
            return decoded
    except Exception as e:
        print(f"[!] Błąd sieci (odbiór): {e}")
        time.sleep(1)
    return b""

def local_to_http(sock):
    while True:
        try:
            data = sock.recv(4096)
            if not data: break
            send_to_relay('c2s', data)
        except Exception as e:
            print(f"[-] Czytanie z terminala przerwane: {e}")
            break

def http_to_local(sock):
    while True:
        data = recv_from_relay('s2c')
        if data:
            try:
                sock.sendall(data)
            except Exception as e:
                print(f"[-] Wypisywanie do terminala przerwane: {e}")
                break
        else:
            time.sleep(0.3)

def start_client():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', LISTEN_PORT))
    server.listen(1)
    
    print(f"[*] Cebula-Relay Klient (Tryb DEBUG) gotowy!")
    print(f"[*] Czekam na połączenie pod: ssh nazwa@127.0.0.1 -p {LISTEN_PORT}")
    
    while True:
        sock, addr = server.accept()
        print(f"\n[+] Połączono z terminalem: {addr}")
        
        try:
            session.get(f"{RELAY_URL}?action=recv&channel=c2s", timeout=3)
            session.get(f"{RELAY_URL}?action=recv&channel=s2c", timeout=3)
        except:
            pass
        
        send_to_relay('c2s', b"---NEW_SSH_SESSION---")
        
        t1 = threading.Thread(target=local_to_http, args=(sock,), daemon=True)
        t2 = threading.Thread(target=http_to_local, args=(sock,), daemon=True)
        t1.start()
        t2.start()

if __name__ == "__main__":
    start_client()