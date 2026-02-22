import socket

import subprocess

import sys

import time

import requests

import psutil

from stun import get_ip_info



from ..client.kcptun_utils import run_kcptun_client, run_kcptun_server



LOCALHOST = "127.0.0.1"

PHP_RENDEZVOUS_URL = "http://16.171.4.247/index.php"

TIMEOUT_IDLE_SECONDS = 300



def register_and_get_peer_name_and_addr(myname, sock, server_addr):

    # zarejestruj się u rendezvous

    sock.sendto(myname.encode(), server_addr)



    print(

        "Sent registration to",

        server_addr,

        # "from local udp port",

        # local_udp_port,

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





def run_ssh_command(user, client_kcptun_port_listen):

    cmd = [

        "ssh",

        "-o",

        "StrictHostKeyChecking=no",

        "-o",

        "UserKnownHostsFile=/dev/null",

        # "-o",

        # f"HostName={host}",

        "-p",

        str(client_kcptun_port_listen),

        f"{user}@{LOCALHOST}",

        # f"{'piotrek'}@{peer_addr[0]}",

    ]



    print(cmd)

    time.sleep(1)

    subprocess.run(cmd)





def run_client(myname, server_addr, local_udp_port, automatic_ssh):

    # UWAGA: server_addr (z CLI) jest ignorowany, bo IP pobieramy dynamicznie z PHP

   

    print(f"\n[{myname}] Pobieram publiczne IP i Port ze STUN (dla portu {local_udp_port})...")

   

    try:

        # Odpytujemy STUN, żeby otworzyć "dziurę" w NAT u klienta

        _, ext_ip, ext_port = get_ip_info('0.0.0.0', local_udp_port, 'stun.l.google.com', 19302)

    except Exception as e:

        print(f"Błąd STUN: {e}")

        sys.exit(1)



    print(f"Moje publiczne IP: {ext_ip}:{ext_port}")

   

    payload = {"user": myname, "ip": ext_ip, "port": ext_port}

    peer_name = None

    peer_addr = None

   

    print(f"Szukam serwera w bazie Rendezvous PHP ({PHP_RENDEZVOUS_URL})...")

   

    # --- FAZA 1: Odpytywanie PHP ---

    while True:

        try:

            res = requests.post(PHP_RENDEZVOUS_URL, json=payload, timeout=5).json()

           

            if res.get("status") == "ok":

                peer_name = res["peername"]

                peer_addr = (res["ip"], int(res["port"]))

                print(f"!!! ZNALEZIONO SERWER !!! -> {peer_name} (celuję w {peer_addr[0]}:{peer_addr[1]})")

                break # Mamy IP serwera, idziemy dalej!

            else:

                print("Czekam na serwer (brak go w bazie PHP)...")

        except Exception as e:

            print(f"Błąd połączenia z PHP: {e}")

       

        time.sleep(3) # Pytamy co 3 sekundy

       

    # --- FAZA 2: KCPTun i SSH ---

    print(f"\nUruchamiam KCPTun Client celując w {peer_addr}...")

   

    # Odpalamy klienta KCPTun (z Twojego pliku kcptun_utils)

    proc = run_kcptun_client(peer_addr, local_kcptun_port=local_udp_port)

   

    try:

        if automatic_ssh:

            print("Daję KCPTunowi 1 sekundę na rozgrzanie tunelu...")

            time.sleep(2)

           

            # Odpalamy SSH (terminal użytkownika zostanie tu przejęty)

            run_ssh_command(peer_name, local_udp_port)

           

            print("\nSesja SSH zakończona.")

        else:

            print("KCPTun działa w tle. Naciśnij Ctrl+C, żeby zamknąć połączenie.")

            proc.wait() # Program "wisi" i podtrzymuje tunel

           

    except KeyboardInterrupt:

        print("\nPrzerwano ręcznie (Ctrl+C).")

       

    finally:

        # --- FAZA 3: Cleanup ---

        print("Zabijam proces KCPTun Clienta...")

        proc.terminate()

        try:

            proc.wait(timeout=3)

        except subprocess.TimeoutExpired:

            proc.kill()

        print("Port zwolniony. Klient wyłączony.")



def run_server(myname, server_addr, listening_port: int):
    while True: # Zewnętrzna pętla maszyny stanów
        print(f"\n[STAN: LISTEN] Nasłuchuję na porcie {listening_port}...")
        peer_name = None

        # --- FAZA 1: Podtrzymanie (Heartbeat) i nasłuchiwanie ---
        while True:
            try:
                # 1. Pobieramy publiczne IP dla naszego lokalnego portu
                _, ext_ip, ext_port = get_ip_info('0.0.0.0', listening_port, 'stun.l.google.com', 19302)
                
                # 2. Rejestrujemy się w bazie PHP na AWS
                payload = {"user": myname, "ip": ext_ip, "port": ext_port}
                res = requests.post(PHP_RENDEZVOUS_URL, json=payload, timeout=5).json()
                
                # 3. Sprawdzamy, czy PHP znalazło dla nas klienta
                if res.get("status") == "ok":
                    peer_name = res["peername"]
                    print(f"!!! ZNALEZIONO KLIENTA !!! -> {peer_name}")
                    break 
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] Heartbeat OK (Mój publiczny port: {ext_port}). Czekam na klienta...")
                
            except Exception as e:
                print(f"Błąd komunikacji STUN/PHP: {e}")
            
            time.sleep(30)

        # --- FAZA 2: KCPTun i Monitorowanie Ruchu ---
        print(f"\n[STAN: CONNECTED] Łączę z {peer_name}. Odpalam KCPTun...")
        
        # Uruchamiamy KCPTun Server
        proc = run_kcptun_server(listening_port=listening_port)
        
        try:
            kcptun_ps = psutil.Process(proc.pid)
            
            # POPRAWKA: Używamy .chars zamiast .bytes, aby widzieć ruch sieciowy (Unix)
            io_start = kcptun_ps.io_counters()
            last_activity = io_start.read_chars + io_start.write_chars
            
            idle_timer = 0
            check_interval = 10 
            
            while True:
                time.sleep(check_interval)
                
                if proc.poll() is not None:
                    print("\nBŁĄD: Proces KCPTun zamknął się niespodziewanie!")
                    break

                try:
                    io_current = kcptun_ps.io_counters()
                    # Sumujemy "chars" - to raportuje aktywność na deskryptorach (sockety)
                    current_activity = io_current.read_chars + io_current.write_chars
                    
                    # Dodatkowa weryfikacja: czy proces ma otwarte jakiekolwiek połączenie UDP?
                    has_network_sockets = len(kcptun_ps.connections(kind='udp')) > 0

                    if current_activity == last_activity or not has_network_sockets:
                        idle_timer += check_interval
                        if idle_timer % 30 == 0: # Loguj co 30s żeby nie śmiecić
                            print(f"Brak realnego ruchu od {idle_timer}s...")
                    else:
                        if idle_timer > 0:
                            print(f"Wykryto aktywność ({current_activity - last_activity} chars). Reset licznika.")
                        idle_timer = 0
                        last_activity = current_activity

                    if idle_timer >= TIMEOUT_IDLE_SECONDS:
                        print(f"\n[TIMEOUT] Brak transferu przez {TIMEOUT_IDLE_SECONDS}s. Zamykam sesję.")
                        break

                except psutil.NoSuchProcess:
                    print("\nBŁĄD: Proces KCPTun zniknął.")
                    break
                    
        finally:
            # --- FAZA 3: Cleanup ---
            print(f"\n[STAN: CLEANUP] Zabijam proces KCPTun (PID: {proc.pid})...")
            
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
            
            print("Port lokalny zwolniony. Powrót do nasłuchiwania...")
            time.sleep(3)