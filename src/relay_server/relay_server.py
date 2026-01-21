# =============================================================================
# TCP RELAY – INSTRUKCJA UŻYCIA (POC, SSH PRZEZ NAT)
#
# Cel:
#   Połączyć dwa komputery (A i B), oba za NAT,
#   przez publiczny serwer relay (R), używając SSH.
#
# Wymagania:
#   - R ma publiczny IP/DNS i otwarty port (domyślnie 5000)
#   - Na A działa sshd
#   - Na A i B dostępne są: ssh, nc (netcat), openssl
#
# -----------------------------------------------------------------------------
# KROK 1: URUCHOM RELAY (R – SERWER PUBLICZNY)
#
#   python3 relay.py
#
#   Sprawdź:
#     ss -lnt | grep 5000
#
# -----------------------------------------------------------------------------
# KROK 2: PRZYGOTUJ MASZYNĘ A (HOST Z SSH, ZA NAT)
#
# 2.1 Wygeneruj session_id (MUSI BYĆ TEN SAM NA A I B):
#
#     SESSION=$(openssl rand -hex 16)
#     echo $SESSION
#
#     Skopiuj SESSION i przenieś na maszynę B.
#
# 2.2 Podłącz A do relay i wystaw sshd przez stdin/stdout:
#
#     printf "%s\n" "$SESSION" | nc relay.example.com 5000 | sshd -i
#
#     Co się dzieje:
#       - nc łączy się do relay
#       - wysyła session_id
#       - sshd -i czyta/pisze przez STDIN/STDOUT
#       - relay forwarduje bajty
#
#     UWAGA:
#       sshd -i NIE nasłuchuje na porcie – to jest tryb inetd.
#
# -----------------------------------------------------------------------------
# KROK 3: POŁĄCZ SIĘ Z MASZYNY B (KLIENT, ZA NAT)
#
#     ssh -o "ProxyCommand=sh -c 'printf \"%s\n\" $SESSION; nc relay.example.com 5000'" user@dummy
#
#     user = użytkownik na maszynie A
#     dummy = dowolna nazwa hosta (ignorowana)
#
# -----------------------------------------------------------------------------
# KROK 4: CO POWINNO SIĘ STAĆ
#
#   - relay sparuje dwa sockety z tym samym session_id
#   - SSH handshake przejdzie
#   - dostaniesz normalny shell z maszyny A
#
# -----------------------------------------------------------------------------
# DEBUG / SANITY CHECK (BEZ SSH)
#
#   Na A:
#     printf "%s\n" "$SESSION" | nc relay.example.com 5000 | nc -l 9000
#
#   Na B:
#     printf "%s\n" "$SESSION" | nc relay.example.com 5000 | nc localhost 9000
#
#   Jeśli echo działa → relay działa poprawnie.
#
# -----------------------------------------------------------------------------
# OGRANICZENIA (POC):
#   - brak auth
#   - brak timeoutów
#   - brak limitów
#   - NIE wystawiać publicznie w tej formie
#
# =============================================================================




import socket
import selectors

HOST = "0.0.0.0"
PORT = 5000
BUF = 4096

sel = selectors.DefaultSelector()

waiting = {}      # session_id -> socket
paired = {}       # socket -> socket
buffers = {}      # socket -> bytes (do czytania session_id)

def close_pair(a):
    b = paired.pop(a, None)
    if b:
        paired.pop(b, None)
        for s in (a, b):
            try:
                sel.unregister(s)
            except Exception:
                pass
            s.close()

def forward(src):
    dst = paired.get(src)
    if not dst:
        return
    try:
        data = src.recv(BUF)
        if not data:
            raise ConnectionError
        dst.sendall(data)
    except Exception:
        close_pair(src)

def handle_client(sock):
    try:
        data = sock.recv(BUF)
        if not data:
            raise ConnectionError
    except Exception:
        sel.unregister(sock)
        sock.close()
        buffers.pop(sock, None)
        return

    buf = buffers.get(sock, b"") + data
    if b"\n" not in buf:
        buffers[sock] = buf
        return

    line, rest = buf.split(b"\n", 1)
    session = line.decode(errors="ignore").strip()

    buffers.pop(sock, None)

    if session in waiting:
        other = waiting.pop(session)
        paired[sock] = other
        paired[other] = sock

        sel.modify(sock, selectors.EVENT_READ, lambda: forward(sock))
        sel.modify(other, selectors.EVENT_READ, lambda: forward(other))

        if rest:
            other.sendall(rest)
    else:
        waiting[session] = sock
        buffers[sock] = b""

def accept(server):
    conn, _ = server.accept()
    conn.setblocking(False)
    buffers[conn] = b""
    sel.register(conn, selectors.EVENT_READ, lambda: handle_client(conn))

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    server.setblocking(False)

    sel.register(server, selectors.EVENT_READ, lambda: accept(server))
    print(f"Relay listening on {PORT}")

    while True:
        for key, _ in sel.select():
            key.data()

if __name__ == "__main__":
    main()





