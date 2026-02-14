# SSH-over-NAT

Challenge is to do achieve something like what you can see in `/archive` folder, but without using zerotier

## How to use

### Prerequisites

- pydoit installed, python-dotenv installed.

On ubuntu

```bash
sudo apt install python3-doit
```

- Rendezvous server running rendezvous.py.

### How to run it?

Start ssh server on the server side of ssh. For example

```bash
sudo systemctl start sshd
```

Then

- server

```bash
doit poc_server
```

- client

```bash
doit poc_client
```

## Advanced usage

For additional info run

```bash
doit help poc_server
```

```bash
doit help poc_client
```
