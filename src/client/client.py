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
            data, addr = self.sock.recvfrom(2048)
            
            if addr == self.server_addr:
                # Message is from the server
                self.handle_server_message(data.decode('utf-8'))
            elif addr == self.peer_addr:
                # Message is from our peer
                print(f"\rPeer: {data.decode('utf-8')}\nYou: ", end="")
            else:
                # An unexpected message
                print(f"\n[*] Received unexpected message from {addr}")

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
                self.peer_addr = (message['ip'], message['port'])
                print(f"\n[SERVER] Peer found at {self.peer_addr}. Punching hole...")
                # Send an initial punch packet to establish the connection
                self.sock.sendto(b'punch', self.peer_addr)
                print("[+] Connection established! You can now send messages.")
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
        while self.peer_addr is None:
            # Wait until the listener gets the peer_info from the server
            time.sleep(1)

        while True:
            try:
                message = input("You: ")
                self.sock.sendto(message.encode('utf-8'), self.peer_addr)
            except KeyboardInterrupt:
                print("\n[*] Exiting.")
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP Hole Punching Client")
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