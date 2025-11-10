# udp_client_v2.py
import socket
import json
import threading
import argparse
import time

class UDPClient:
    def __init__(self, server_ip, server_port):
        self.server_addr = (server_ip, server_port)
        self.peer_addr = None
        
        # --- NEW LOGIC FOR SYMMETRIC NAT ---
        self.peer_ip = None                 # Store just the IP after introduction
        self.peer_addr_confirmed = False    # Flag to lock in the peer address once we hear from them
        # ------------------------------------

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0)) # Bind to a random available port
        self.listener_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        self.listener_thread.start()

    def send_json(self, data):
        """Utility to send JSON to the central server."""
        self.sock.sendto(json.dumps(data).encode('utf-8'), self.server_addr)

    def listen_for_messages(self):
        """Runs in a background thread to process all incoming messages."""
        while True:
            try:
                data, addr = self.sock.recvfrom(2048)
                decoded_data = data.decode('utf-8')

                if addr == self.server_addr:
                    # Message is from the server
                    self.handle_server_message(decoded_data)

                # --- MODIFIED LOGIC TO HANDLE SYMMETRIC NAT ---
                elif not self.peer_addr_confirmed and self.peer_ip is not None and addr[0] == self.peer_ip:
                    # This is the FIRST message we have received from our peer's IP.
                    # This is their REAL address. Trust it and lock it in.
                    print(f"\n[+] NAT detected. Peer's real address is {addr}. Locking in.")
                    self.peer_addr = addr
                    self.peer_addr_confirmed = True
                    print(f"\rPeer: {decoded_data}\nYou: ", end="")
                
                elif addr == self.peer_addr:
                    # This is a subsequent message from the confirmed peer.
                    print(f"\rPeer: {decoded_data}\nYou: ", end="")
                # --------------------------------------------
                else:
                    # An unexpected message from an unknown source
                    print(f"\n[*] Received unexpected message from {addr}")

            except Exception as e:
                print(f"\n[!] An error occurred in the listener thread: {e}")
                break

    def handle_server_message(self, message_str):
        """Parses messages from the server and acts accordingly."""
        try:
            message = json.loads(message_str)
            status = message.get('status')
            
            if status == 'register_success':
                print(f"[SERVER] {message.get('message')}")
            elif status == 'login_success':
                print(f"[SERVER] {message.get('message')}")
            elif status == 'peer_info':
                # --- MODIFIED LOGIC ---
                # Store the server's guess and the IP separately
                self.peer_addr = (message['ip'], message['port'])
                self.peer_ip = message['ip'] 
                # -----------------------
                print(f"\n[SERVER] Peer initially reported at {self.peer_addr}. Punching hole...")
                # Send an initial punch packet to the server's guessed address
                self.sock.sendto(b'punch', self.peer_addr)
                print("[+] Waiting for peer's response to confirm final address...")
            elif status == 'error':
                print(f"[SERVER ERROR] {message.get('message')}")
        except json.JSONDecodeError:
            print(f"[!] Could not decode server message: {message_str}")

    def register(self, username, password):
        print(f"[*] Sending registration request for '{username}'...")
        self.send_json({
            "command": "register",
            "username": username,
            "password": password
        })
        time.sleep(2) # Wait a moment for the server's reply

    def login(self, username, password, peer_name):
        print(f"[*] Sending login request for '{username}', seeking '{peer_name}'...")
        self.send_json({
            "command": "login",
            "username": username,
            "password": password,
            "peer_name": peer_name
        })
        self.start_chat_loop()

    def start_chat_loop(self):
        """Main loop for sending messages to the peer."""
        # First, wait until the listener gets the initial peer_info from the server
        while self.peer_ip is None:
            time.sleep(0.5)

        # --- MODIFIED LOGIC ---
        # Now, wait until the peer address is confirmed by their first message
        timeout = 20 # seconds
        start_time = time.time()
        while not self.peer_addr_confirmed:
            if time.time() - start_time > timeout:
                print("\n[!] Timed out waiting for peer. They might be offline or behind an incompatible NAT.")
                return
            
            print(f"[*] Waiting for first message from peer to confirm connection...", end='\r')
            # Periodically resend the punch packet in case it gets lost
            if self.peer_addr:
                self.sock.sendto(b'punch', self.peer_addr)
            time.sleep(2)
        # --------------------
        
        print("\n[+] Connection confirmed! You can now send messages.")
        while True:
            try:
                message = input("You: ")
                if self.peer_addr:
                    self.sock.sendto(message.encode('utf-8'), self.peer_addr)
            except KeyboardInterrupt:
                print("\n[*] Exiting.")
                break
            except Exception as e:
                print(f"\n[!] An error occurred while sending: {e}")
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="UDP Hole Punching Client with Authentication",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("command", choices=['register', 'login'], help="Action to perform")
    parser.add_argument("-s", "--server", required=True, help="IP address of the rendezvous server")
    parser.add_argument("-u", "--username", required=True, help="Your username")
    parser.add_argument("-p", "--password", required=True, help="Your password")
    parser.add_argument("--peer", help="The username of the peer you want to connect to (required for login)")

    args = parser.parse_args()

    client = UDPClient(args.server, 50)

    if args.command == 'register':
        client.register(args.username, args.password)
    elif args.command == 'login':
        if not args.peer:
            parser.error("--peer is required for the login command")
        client.login(args.username, args.password, args.peer)