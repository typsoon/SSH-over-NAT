import socket
import paramiko as pa
from paramiko import Transport, RSAKey, ECDSAKey, Ed25519Key
import paramiko.common as pacom
import logging
from typing import Optional
import threading
import os
import subprocess


KEY_PATH = "my_server_key"

host_key: Optional[pa.RSAKey] = None
try:
    host_key = pa.RSAKey(filename=KEY_PATH)
except FileNotFoundError:
    print("[Server] Error: 'test_rsa.key' not found. Run ssh-keygen first.")
    exit(1)

# OR generate one if you don't have it
# host_key = Ed25519Key.generate(bits=256)
pa.util.log_to_file("paramiko_debug.log", level=logging.DEBUG)


class KeyAuthServer(pa.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    # 1. Tell the client we accept public keys!
    def get_allowed_auths(self, username):
        return "publickey"  # <--- THIS WAS MISSING

    def check_channel_request(self, kind, chanid):
        return (
            pacom.OPEN_SUCCEEDED
            if kind == "session"
            else pacom.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
        )

    def check_auth_publickey(self, username, key):
        if username == "ubuntu":  # Make sure this matches your client call
            # (Add your key verification logic here as discussed before)
            return pacom.AUTH_SUCCESSFUL
        return pacom.AUTH_FAILED

    def check_channel_pty_request(
        self, channel, term, width, height, pixelwidth, pixelheight, modes
    ):
        # Return True to say "Yes, I allow a terminal"
        return True

    def check_channel_shell_request(self, channel):
        self.event.set()  # Mark that the shell is ready
        return True  # Allow Shell


def create_client_session(sock_to_client: socket.socket):
    transp = pa.Transport(conn)

    assert host_key is not None
    transp.add_server_key(host_key)

    # print("--- DEBUGGING KEYS ---")
    # # 1. Ask Paramiko what IT supports by default
    # available_server_keys = list(
    #     filter(
    #         list(transp.server_key_dict.keys()).__contains__,
    #         transp.preferred_keys,
    #     )
    # )
    # print(
    #     f"Server (Me) supports: {available_server_keys} {transp.preferred_keys} {(list(transp.server_key_dict.keys()),)}"
    # )
    #
    server = KeyAuthServer()

    try:
        transp.start_server(server=server)

        # 1. Accept the new channel
        channel = transp.accept(20)
        if channel is None:
            print("Client did not open a channel.")
            exit(1)

        # 2. Wait for the Client to ask for a Shell (Wait for check_channel_shell_request)
        print("[Server] Authenticated. Waiting for Shell request...")
        server.event.wait(10)  # Wait up to 10 seconds
        if not server.event.is_set():
            print("[Server] Client never asked for a shell.")
            exit(1)

        channel.send(b"Welcome to the Interactive Python Shell!\r\n")

        # 3. INTERACTIVE LOOP (The Fix)
        # Instead of closing, we loop forever reading data
        while True:
            # 1. Receive command
            command_bytes = channel.recv(1024)
            if not command_bytes:
                print("Client disconnected.")
                break

            command = command_bytes.decode().strip()
            print(f"[Server] Executing: {command}")

            # 2. Handle 'exit'
            if command.lower() == "exit":
                break

            # 3. Handle 'cd' (Change Directory)
            # 'cd' must be done in the main python process, not a subprocess
            if command.startswith("cd "):
                try:
                    target_dir = command[3:].strip()
                    os.chdir(target_dir)  # Change folder
                    output = f"Changed directory to: {os.getcwd()}\n"
                except FileNotFoundError:
                    output = f"Directory not found: {target_dir}\n"
                except Exception as e:
                    output = f"Error: {e}\n"

            # 4. Execute standard commands (ls, pwd, etc.)
            else:
                try:
                    # shell=True allows using pipes and wildcards
                    result = subprocess.run(
                        command, shell=True, capture_output=True, text=True
                    )
                    # Combine Standard Output and Standard Error
                    output = result.stdout + result.stderr
                except Exception as e:
                    output = f"Execution failed: {str(e)}\n"

            # 5. Send result back to client
            # If output is empty (some commands have no output), send a prompt
            if not output:
                output = "Done.\n"

            channel.send(output.encode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        transp.close()


if __name__ == "__main__":
    server_sock = socket.create_server(("0.0.0.0", 50))
    conn, address = server_sock.accept()
    create_client_session(conn)
