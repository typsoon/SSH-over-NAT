import socket
import paramiko
import time
import sys
import threading
import cmd

server_ip = "13.61.13.117"
server_port = 50


class RemoteShell(cmd.Cmd):
    prompt = "superkomputer:~# "  # Your custom prompt
    intro = "Connected! Type 'exit' to disconnect."

    def __init__(self, channel):
        super().__init__()
        self.channel = channel

    def default(self, line):
        """Sends any command typed by the user to the server."""
        if line:
            try:
                # Send the command + newline
                self.channel.send(f"{line}\n".encode())
            except Exception as e:
                print(f"\nError sending command: {e}")
                # return True  # Stop the loop

    def do_exit(self, arg):
        """Stops the shell when you type 'exit'."""
        return True  # Returning True breaks the cmdloop

    def do_EOF(self, arg):
        """Handles Ctrl+D to exit cleanly."""
        print()
        return True

    # def emptyline(self):
    #     """Prevents repeating the last command if you just hit Enter."""
    #     pass


def create_session(sock: socket.socket):
    # transp = pa.Transport(sock)
    #
    # transp.start_client()

    client = paramiko.SSHClient()

    # 1. Trust the local server key automatically
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.load_system_host_keys()
    client.connect(
        server_ip, server_port, "ubuntu", key_filename="my_server_key", sock=sock
    )

    print("Connected")

    channel = client.invoke_shell()

    def listen_to_server(channel):
        while True:
            try:
                if channel.recv_ready():
                    data = channel.recv(1024)
                    if not data:
                        break
                    # Write directly to stdout so it mixes well with the prompt
                    sys.stdout.write(data.decode())
                    sys.stdout.flush()
                else:
                    time.sleep(0.1)
            except OSError:
                break
            except Exception:
                break

    # --- PUT THIS WHERE YOUR OLD LOOP WAS ---

    # 1. Start the listener thread
    t = threading.Thread(target=listen_to_server, args=(channel,))
    t.daemon = True
    t.start()

    # 2. Start the improved Input Loop
    try:
        shell = RemoteShell(channel)
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\nClosing connection...")

    client.close()


if __name__ == "__main__":
    sock = socket.create_connection((server_ip, server_port))
    create_session(sock)
