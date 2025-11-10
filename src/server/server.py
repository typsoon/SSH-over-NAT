# udp_server_v2.py
import socket
import json
import database as db

class UDPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # This dictionary will map a logged-in username to their address (ip, port)
        self.logged_in_clients = {}

    def start(self):
        """Binds the server and starts the main listening loop."""
        db.setup_database()
        self.sock.bind((self.host, self.port))
        print(f"[*] UDP Server started on {self.host}:{self.port}")

        while True:
            try:
                data, addr = self.sock.recvfrom(2048)
                self.handle_message(data, addr)
            except Exception as e:
                print(f"[!] An error occurred in the main loop: {e}")

    def send_json(self, data, addr):
        """Utility function to send a JSON payload to an address."""
        self.sock.sendto(json.dumps(data).encode('utf-8'), addr)

    def handle_message(self, data, addr):
        """Processes incoming messages based on their command."""
        try:
            message = json.loads(data.decode('utf-8'))
            command = message.get('command')

            if command == 'register':
                self.handle_register(message, addr)
            elif command == 'login':
                self.handle_login(message, addr)
            else:
                self.send_json({"status": "error", "message": "Invalid command"}, addr)

        except json.JSONDecodeError:
            print(f"[!] Received malformed JSON from {addr}")
        except Exception as e:
            print(f"[!] Error handling message from {addr}: {e}")

    def handle_register(self, message, addr):
        """Handles a user registration request."""
        username = message.get('username')
        password = message.get('password')
        if not username or not password:
            self.send_json({"status": "error", "message": "Username and password required"}, addr)
            return

        print(f"[*] Received registration request for '{username}' from {addr}")
        if db.add_user(username, password):
            self.send_json({"status": "register_success", "message": "Registration successful"}, addr)
        else:
            self.send_json({"status": "error", "message": "Username already exists"}, addr)

    def handle_login(self, message, addr):
        """Handles a user login request and triggers peer introduction if possible."""
        username = message.get('username')
        password = message.get('password')
        peer_name = message.get('peer_name')

        if not username or not password or not peer_name:
            self.send_json({"status": "error", "message": "Username, password, and peer_name required"}, addr)
            return

        print(f"[*] Received login request from '{username}' for peer '{peer_name}'")
        if db.authenticate_user(username, password):
            self.logged_in_clients[username] = addr
            self.send_json({"status": "login_success", "message": "Login successful. Waiting for peer."}, addr)
            
            # CRITICAL STEP: Check if the desired peer is also logged in
            if peer_name in self.logged_in_clients:
                self.introduce_peers(username, peer_name)
        else:
            self.send_json({"status": "error", "message": "Invalid username or password"}, addr)

    def introduce_peers(self, user1_name, user2_name):
        """Sends connection info to two logged-in clients."""
        print(f"[*] Match found! Introducing '{user1_name}' and '{user2_name}'.")
        user1_addr = self.logged_in_clients[user1_name]
        user2_addr = self.logged_in_clients[user2_name]

        # Send user2's info to user1
        intro_for_user1 = {"status": "peer_info", "ip": user2_addr[0], "port": user2_addr[1]}
        self.send_json(intro_for_user1, user1_addr)

        # Send user1's info to user2
        intro_for_user2 = {"status": "peer_info", "ip": user1_addr[0], "port": user1_addr[1]}
        self.send_json(intro_for_user2, user2_addr)

if __name__ == "__main__":
    server = UDPServer('0.0.0.0', 50)
    server.start()