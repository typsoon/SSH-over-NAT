from pathlib import Path

import psutil

kcptun_dir_path = Path(__file__).parents[1].resolve() / "kcptun_bin"

if not kcptun_dir_path.exists():
    raise RuntimeError(f"Kcptun binaries folder not found under {kcptun_dir_path}")

kcptun_client_path = kcptun_dir_path / "client_linux_amd64"
kcptun_server_path = kcptun_dir_path / "server_linux_amd64"


def run_kcptun_client(
    peer_addr, local_kcptun_port=8080, key: str = "mysecret"
) -> psutil.Popen:
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
    return psutil.Popen(cmd)


def run_kcptun_server(
    target_addr=("127.0.0.1", 22), listening_port=5050, key: str = "mysecret"
) -> psutil.Popen:
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
    return psutil.Popen(cmd)


# sudo ./server_linux_amd64 -l :50 -t 127.0.0.1:22 --key "mysecret
