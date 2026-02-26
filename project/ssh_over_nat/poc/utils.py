from signal import SIGINT
import socket
import subprocess
import sys
import time
import requests
import psutil

from stun import get_ip_info
from ..common import LOCALHOST, PHP_RENDEZVOUS_URL_FMSTR

from ..relay_php import start_relay_client, start_relay_server
from ..client.kcptun_utils import run_kcptun_client, run_kcptun_server


TIMEOUT_IDLE_SECONDS = 300
SSH_TIMEOUT = 4

KCPTUN_WARMUP = 2


def end_proc(proc):
    proc.send_signal(SIGINT)
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()


def register_and_get_peer_name_and_addr(myname, sock, server_addr):
    sock.sendto(myname.encode(), server_addr)
    print(
        "Sent registration to",
        server_addr,
    )

    try:
        data, addr = sock.recvfrom(1024)
    except socket.timeout:
        print("No reply from rendezvous")
        sys.exit(2)

    reply = data.decode().strip().split()
    peername, peer_ip, peer_port = reply[0], reply[1], int(reply[2])
    print("Got peer:", peername, peer_ip, peer_port)
    peer_addr = (peer_ip, peer_port)

    return peername, peer_addr


def run_ssh_command(user, client_kcptun_port_listen, timeout=None):
    cmd = get_ssh_command(user, client_kcptun_port_listen, timeout)

    print(cmd)
    time.sleep(1)
    subprocess.run(cmd)


def get_ssh_command(user, client_kcptun_port_listen, timeout) -> list[str]:
    options = [
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-p",
        str(client_kcptun_port_listen),
    ]
    if timeout is not None:
        options += ["-o", f"ConnectTimeout={timeout}"]

    cmd = ["ssh"] + options + [f"{user}@{LOCALHOST}"]
    # f"{'piotrek'}@{peer_addr[0]}",
    return cmd


def check_if_ssh_is_possible(user, client_kcptun_port_listen, timeout=SSH_TIMEOUT):
    cmd = get_ssh_command(user, client_kcptun_port_listen, timeout)
    with subprocess.Popen(cmd) as ssh_proc:
        try:
            ssh_proc.wait(timeout=timeout + 1)
        except subprocess.TimeoutExpired:
            # print(f"AHA {e}", type(e))
            ssh_proc.send_signal(SIGINT)
            return True
        return False


def run_client(hash, server_addr, local_udp_port, automatic_ssh, username):
    PHP_RENDEZVOUS_URL = PHP_RENDEZVOUS_URL_FMSTR % server_addr[0]

    print(
        f"\n[{hash}]\n Pobieram publiczne IP i Port ze STUN (dla portu {local_udp_port})..."
    )

    try:
        # Odpytujemy STUN, żeby otworzyć "dziurę" w NAT u klienta
        _, ext_ip, ext_port = get_ip_info(
            "0.0.0.0", local_udp_port, "stun.l.google.com", 19302
        )
    except Exception as e:
        print(f"Błąd STUN: {e}")
        sys.exit(1)

    print(f"Moje publiczne IP: {ext_ip}:{ext_port}")

    payload = {"hash": hash, "ip": ext_ip, "port": ext_port}
    peer_hash = None
    peer_addr = None

    print(f"Szukam serwera w bazie Rendezvous PHP ({PHP_RENDEZVOUS_URL})...")

    # --- FAZA 1: Odpytywanie PHP ---

    while True:
        try:
            res = requests.post(PHP_RENDEZVOUS_URL, json=payload, timeout=5).json()

            if res.get("status") == "ok":
                peer_hash = res["peerhash"]
                peer_addr = (res["ip"], int(res["port"]))
                print(
                    f"!!! ZNALEZIONO SERWER !!! -> {peer_hash}\n    (celuję w {peer_addr[0]}:{peer_addr[1]})"
                )
                break  # Mamy IP serwera, idziemy dalej!
            else:
                print("Czekam na serwer (brak go w bazie PHP)...")
        except Exception as e:
            print(f"Błąd połączenia z PHP: {e}")

        time.sleep(3)  # Pytamy co 3 sekundy

    # --- FAZA 2: KCPTun i SSH ---
    print(f"\nUruchamiam KCPTun Client celując w {peer_addr}...")

    # Odpalamy klienta KCPTun (z Twojego pliku kcptun_utils)
    with run_kcptun_client(peer_addr, local_kcptun_port=local_udp_port) as proc:
        try:
            print(f"Daję KCPTunowi {KCPTUN_WARMUP} sekundy na rozgrzanie tunelu...")
            time.sleep(KCPTUN_WARMUP)

            is_possible = check_if_ssh_is_possible(
                username, local_udp_port, timeout=SSH_TIMEOUT
            )
            if is_possible:
                if automatic_ssh:
                    # Odpalamy SSH (terminal użytkownika zostanie tu przejęty)
                    run_ssh_command(username, local_udp_port)

                    print("\nSesja SSH zakończona.")
                else:
                    print(
                        "KCPTun działa w tle. Naciśnij Ctrl+C, żeby zamknąć połączenie."
                    )
            else:
                print("SSH nie jest możliwe, przełaczam się na relay")
                end_proc(proc)

                import multiprocessing

                relay_cl = multiprocessing.Process(target=start_relay_client)

                try:
                    relay_cl.start()
                    if automatic_ssh:
                        # Odpalamy SSH (terminal użytkownika zostanie tu przejęty)
                        run_ssh_command(username, local_udp_port)
                        print("\nSesja SSH zakończona.")
                    else:
                        print(
                            "Klient relay dzia w tle. Naciśnij Ctrl+C, żeby zamknąć połączenie."
                        )
                except KeyboardInterrupt:
                    print("\nPrzerwano ręcznie (Ctrl+C).")
                    print("Zabijam klienta relay")
                    relay_cl.kill()

        except KeyboardInterrupt:
            print("\nPrzerwano ręcznie (Ctrl+C).")
            print("Zabijam proces KCPTun Clienta...")
            end_proc(proc)

        print("Port zwolniony. Klient wyłączony.")


def run_server(hash, server_addr, listening_port: int):
    PHP_RENDEZVOUS_URL = PHP_RENDEZVOUS_URL_FMSTR % server_addr[0]
    while True:  # Zewnętrzna pętla maszyny stanów
        print(f"\n[STAN: LISTEN] Nasłuchuję na porcie {listening_port}...")
        peer_hash = None

        # --- FAZA 1: Podtrzymanie (Heartbeat) i nasłuchiwanie ---
        while True:
            try:
                # 1. Pobieramy publiczne IP dla naszego lokalnego portu
                _, ext_ip, ext_port = get_ip_info(
                    source_port=listening_port,
                    stun_host="stun.l.google.com",
                    stun_port=19302,
                )

                # 2. Rejestrujemy się w bazie PHP na AWS
                payload = {"hash": hash, "ip": ext_ip, "port": ext_port}
                res = requests.post(PHP_RENDEZVOUS_URL, json=payload, timeout=5).json()

                # 3. Sprawdzamy, czy PHP znalazło dla nas klienta
                if res.get("status") == "ok":
                    peer_hash = res["peerhash"]
                    print(f"!!! ZNALEZIONO KLIENTA !!! -> {peer_hash}")
                    break
                else:
                    print(
                        f"[{time.strftime('%H:%M:%S')}] Heartbeat OK (Mój publiczny port: {ext_port}). Czekam na klienta..."
                    )

            except Exception as e:
                print(f"Błąd komunikacji STUN/PHP: {e}")

            time.sleep(3)

        # --- FAZA 2: KCPTun i Monitorowanie Ruchu ---
        print("\n[STAN: CONNECTED] Łączę z klientem. Odpalam KCPTun...")

        # Uruchamiamy KCPTun Server
        with run_kcptun_server(listening_port=listening_port) as proc:
            try:
                print(f"Daję KCPTunowi {KCPTUN_WARMUP} sekundy na rozgrzanie tunelu...")
                time.sleep(KCPTUN_WARMUP)
                # POPRAWKA: Używamy .chars zamiast .bytes, aby widzieć ruch sieciowy (Unix)

                io_start = proc.io_counters()
                last_activity = io_start.read_chars + io_start.write_chars

                print("Waiting for ssh connection from client")
                time.sleep(SSH_TIMEOUT + 1)

                io_current = proc.io_counters()
                # Sumujemy "chars" - to raportuje aktywność na deskryptorach (sockety)
                current_activity = io_current.read_chars + io_current.write_chars

                # Dodatkowa weryfikacja: czy proces ma otwarte jakiekolwiek połączenie UDP?
                has_network_sockets = len(proc.net_connections(kind="udp")) > 0

                if current_activity == last_activity or not has_network_sockets:
                    print(
                        "Client failed to verify if ssh is possible. Falling back to relay"
                    )

                    end_proc(proc)

                    start_relay_server(server_addr[0])

                    break

                idle_timer = 0
                check_interval = 10

                while True:
                    time.sleep(check_interval)
                    if proc.poll() is not None:
                        print("\nBŁĄD: Proces KCPTun zamknął się niespodziewanie!")
                        break

                    io_current = proc.io_counters()
                    # Sumujemy "chars" - to raportuje aktywność na deskryptorach (sockety)
                    current_activity = io_current.read_chars + io_current.write_chars

                    # Dodatkowa weryfikacja: czy proces ma otwarte jakiekolwiek połączenie UDP?
                    has_network_sockets = len(proc.net_connections(kind="udp")) > 0

                    if current_activity == last_activity or not has_network_sockets:
                        idle_timer += check_interval
                        if idle_timer % 30 == 0:  # Loguj co 30s żeby nie śmiecić
                            print(f"Brak realnego ruchu od {idle_timer}s...")
                    else:
                        if idle_timer > 0:
                            print(
                                f"Wykryto aktywność ({current_activity - last_activity} chars). Reset licznika."
                            )
                        idle_timer = 0
                        last_activity = current_activity

                    if idle_timer >= TIMEOUT_IDLE_SECONDS:
                        print(
                            f"\n[TIMEOUT] Brak transferu przez {TIMEOUT_IDLE_SECONDS}s. Zamykam sesję."
                        )
                        break

            except psutil.NoSuchProcess:
                print("\nBŁĄD: Proces KCPTun zniknął.")
                break
            finally:
                # --- FAZA 3: Cleanup ---
                print(f"\n[STAN: CLEANUP] Zabijam proces KCPTun (PID: {proc.pid})...")

                print("Port lokalny zwolniony. Powrót do nasłuchiwania...")
                time.sleep(3)
