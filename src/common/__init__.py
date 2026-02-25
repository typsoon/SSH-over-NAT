import os
from dotenv import load_dotenv

load_dotenv()

SOCKET_PATH = "/tmp/ssh-over-nat-socket-123123123"
DEFAULT_SERVER_IP = os.getenv("REMOTE_SERVER_IP")
DEFAULT_SERVER_PORT = int(os.getenv("REMOTE_UDP_PORT", 50))
DEFAULT_LOCAL_PORT_FOR_SRV_MODE = 8025
DEFAULT_LOCAL_PORT_FOR_CLIENT_MODE = 8022

PHP_RENDEZVOUS_URL = f"http://{DEFAULT_SERVER_IP}/index.php"
