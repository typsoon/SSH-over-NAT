import socket
import threading
import time
import requests
import base64

RELAY_URL = "http://16.171.4.247/relay.php"  # <--- PODMIEŃ
SSH_PORT = 22

session = requests.Session()
current_sock = None

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

def ssh_to_http(sock):
    while True:
        try:
            data = sock.recv(4096)
            if not data: break
            send_to_relay('s2c', data)
        except Exception as e:
            print(f"[-] Połączenie z SSH przerwane: {e}")
            break

def main_loop():
    global current_sock
    print(f"[*] Cebula-Relay Serwer (Tryb DEBUG) gotowy na: {RELAY_URL}")
    
    while True:
        data = recv_from_relay('c2s')
        if data:
            # POPRAWKA: Szukamy sygnału W ŚRODKU paczki, bo PHP mogło to skleić z danymi SSH!
            if b"---NEW_SSH_SESSION---" in data:
                print("\n[+] [SYGNAŁ] Żądanie nowego połączenia! Otwieram SSH...")
                
                if current_sock:
                    try: current_sock.close()
                    except: pass
                
                current_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    current_sock.connect(('127.0.0.1', SSH_PORT))
                    threading.Thread(target=ssh_to_http, args=(current_sock,), daemon=True).start()
                except Exception as e:
                    print(f"[!] BŁĄD SSH: {e}")
                    continue # Nie idź dalej, jeśli SSH leży
                
                # Usuwamy sygnał z danych. Jeśli zostało coś jeszcze (np. baner SSH), pchamy to dalej!
                data = data.replace(b"---NEW_SSH_SESSION---", b"")
                if len(data) > 0:
                    print(f"[DEBUG] Po usunięciu sygnału zostało {len(data)} bajtów. Wpycham do SSH.")
                    current_sock.sendall(data)
            else:
                # Zwykłe dane
                if current_sock:
                    try:
                        current_sock.sendall(data)
                    except Exception as e:
                        print(f"[!] Nie udało się wcisnąć do SSH: {e}")
        else:
            time.sleep(0.3)

if __name__ == "__main__":
    main_loop()