import subprocess
from pathlib import Path

kcptun_dir_path = Path("../kcptun")
kcptun_client_path = kcptun_dir_path / "client_linux_amd64"
kcptun_server_path = kcptun_dir_path / "server_linux_amd64"


def run_client(peer_addr, local_kcptun_port=8080, key: str = "mysecret"):
    peer_host, peer_port = peer_addr
    cmd = [
        kcptun_client_path,
        "-r",
        f"{peer_host}:{peer_port}",
        "-l",
        f":{local_kcptun_port}",
        # "--key",
        # key,
    ]
    print(cmd)
    subprocess.run(cmd)


def run_server(
    target_addr=("127.0.0.1", 22), listening_port=5050, key: str = "mysecret"
):
    target_host, target_port = target_addr
    cmd = [
        kcptun_server_path,
        "-l",
        f":{listening_port}",
        "-t",
        f"{target_host}:{target_port}",
        # "--key",
        # key,
    ]
    print(cmd)
    subprocess.run(cmd)


# sudo ./server_linux_amd64 -l :50 -t 127.0.0.1:22 --key "mysecret
