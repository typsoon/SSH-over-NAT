# SSH-over-NAT

## Installation

### Locally via pip

At project root run

```python
python -m pip install .
```

## How to run it?

### Prerequisites

- Rendezvous server running apache2 with hashed.php and relay.php uploaded to it

Start ssh server on the server side of ssh. For example

```bash
sudo systemctl start sshd
```

Then

- server

```bash
ssh-over-nat poc_server
```

- client

```bash
ssh-over-nat poc_client
```

## Advanced usage

For additional info run

```bash
ssh-over-nat list
ssh-over-nat help
ssh-over-nat help poc_server
ssh-over-nat help poc_client
ssh-over-nat help run_ssh_command
ssh-over-nat help environment
