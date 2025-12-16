# rendezvous.py
import socket
import threading
import time

PORT = 50
clients = {}  # name -> (ip, port, last_seen)

lock = threading.Lock()

def cleaner():
    while True:
        time.sleep(30)
        with lock:
            now = time.time()
            for k in list(clients.keys()):
                if now - clients[k][2] > 120:
                    del clients[k]

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", PORT))
    print("Rendezvous server listening on UDP port", PORT)
    threading.Thread(target=cleaner, daemon=True).start()

    while True:
        data, addr = sock.recvfrom(1024)
        name = data.decode().strip()
        with lock:
            clients[name] = (addr[0], addr[1], time.time())
            print("register:", name, "->", addr)
            # jeśli są co najmniej 2 klientów, wyślij każdemu info o pozostałych
            if len(clients) >= 2:
                names = list(clients.keys())
                for n in names:
                    others = [x for x in names if x != n]
                    if others:
                        ox, op, _ = clients[others[0]]
                        msg = f"{others[0]} {ox} {op}"
                        sock.sendto(msg.encode(), (clients[n][0], clients[n][1]))

if __name__ == "__main__":
    main()
