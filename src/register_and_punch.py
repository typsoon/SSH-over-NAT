# register_and_punch.py
import socket, sys, time, threading

if len(sys.argv) != 5:
    print("Usage: python3 register_and_punch.py <myname> <vps_ip> <vps_port> <local_udp_port>")
    sys.exit(1)

myname = sys.argv[1]
vps_ip = sys.argv[2]
vps_port = int(sys.argv[3])
local_udp_port = int(sys.argv[4])

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", local_udp_port))   # ważne: wiążemy lokalny UDP port, który będzie źródłowym mappingiem
sock.settimeout(10)

# zarejestruj się u rendezvous
sock.sendto(myname.encode(), (vps_ip, vps_port))
print("Sent registration to", vps_ip, vps_port, "from local udp port", local_udp_port)

try:
    data, addr = sock.recvfrom(1024)
except socket.timeout:
    print("No reply from rendezvous")
    sys.exit(2)

reply = data.decode().strip().split()
peername, peer_ip, peer_port = reply[0], reply[1], int(reply[2])
print("Got peer:", peername, peer_ip, peer_port)

# funkcja pingująca peer co 1s, aby utrzymać NAT mapping
def punch_loop():
    while True:
        try:
            sock.sendto(b"punch", (peer_ip, peer_port))
        except Exception as e:
            print("Punch send error:", e)
        time.sleep(1)

t = threading.Thread(target=punch_loop, daemon=True)
t.start()

print("Punching in background. Keep this running. Local UDP bound to", local_udp_port)
print("Peer:", peer_ip, peer_port)
# program zostaje uruchomiony w tle — możesz ctrl+c żeby przerwać
while True:
    time.sleep(3600)
