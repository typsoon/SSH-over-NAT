#!/usr/bin/env python3
import socket
import threading

waiting = None  # pierwszy klient, który czeka na parę

def relay(a, b, label):
    try:
        while True:
            data = a.recv(4096)
            if not data:
                print(f"[relay-{label}] closed")
                break
            b.sendall(data)
    except Exception as e:
        print(f"[relay-{label}] error: {e}")
    finally:
        try: a.close()
        except: pass
        try: b.close()
        except: pass

def handler(conn, addr):
    global waiting
    print(f"[client] connected from {addr}")

    if waiting is None:
        waiting = conn
        print(f"[waiting] client {addr} is waiting for a peer")
    else:
        first = waiting
        second = conn
        waiting = None

        print(f"[pair] connecting {first.getpeername()} <-> {second.getpeername()}")
        threading.Thread(target=relay, args=(first, second, "A→B"), daemon=True).start()
        threading.Thread(target=relay, args=(second, first, "B→A"), daemon=True).start()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 5000))
    server.listen()
    print("[server] started on port 5000")

    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handler, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("[server] shutting down")
    finally:
        server.close()

if __name__ == "__main__":
    main()
