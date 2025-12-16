# udp_tcp_bridge.py
# Usage:
#  python3 udp_tcp_bridge.py --local-tcp 22 --local-udp 40000 --peer-ip <peer_ip> --peer-port <peer_port>
#  python3 udp_tcp_bridge.py --local-tcp 5022 --local-udp 40000 --peer-ip <peer_ip> --peer-port <peer_port>

import socket, threading, argparse, sys

def handle_conn(tcp_conn, peer_ip, peer_port, local_udp_port):
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(('', local_udp_port))   # ważne: bindujemy ten sam lokalny UDP port
    udp.settimeout(1.0)

    alive = True

    def tcp_to_udp():
        nonlocal alive
        try:
            while alive:
                data = tcp_conn.recv(4096)
                if not data:
                    break
                udp.sendto(data, (peer_ip, peer_port))
        except Exception as e:
            # print("tcp->udp", e)
            pass
        alive = False

    def udp_to_tcp():
        nonlocal alive
        try:
            while alive:
                try:
                    data, addr = udp.recvfrom(65536)
                except socket.timeout:
                    continue
                # akceptuj tylko dane od peer
                if addr[0] == peer_ip and addr[1] == peer_port:
                    try:
                        tcp_conn.sendall(data)
                    except Exception:
                        break
        except Exception as e:
            # print("udp->tcp", e)
            pass
        alive = False

    t1 = threading.Thread(target=tcp_to_udp, daemon=True)
    t2 = threading.Thread(target=udp_to_tcp, daemon=True)
    t1.start(); t2.start()
    t1.join(); t2.join()
    try:
        tcp_conn.close()
    except:
        pass
    try:
        udp.close()
    except:
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-tcp", type=int, required=True)
    parser.add_argument("--local-udp", type=int, required=True)
    parser.add_argument("--peer-ip", required=True)
    parser.add_argument("--peer-port", type=int, required=True)
    args = parser.parse_args()

    # listen for local TCP connections
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('127.0.0.1', args.local_tcp))
    srv.listen(1)
    print(f"Bridge listening on TCP 127.0.0.1:{args.local_tcp} and UDP local port {args.local_udp}. Forwarding to {args.peer_ip}:{args.peer_port}")
    while True:
        conn, addr = srv.accept()
        print("Accepted local TCP conn from", addr)
        thr = threading.Thread(target=handle_conn, args=(conn, args.peer_ip, args.peer_port, args.local_udp), daemon=True)
        thr.start()

if __name__ == "__main__":
    main()
