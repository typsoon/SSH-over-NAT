# SSH-over-NAT
You need to create an account on https://www.zerotier.com/.

Then create a network and make it public(it is optional, otherwise you need to accept each device that is connect to your network).

Then you copy Network ID and it will be used after option -j.

Running:

sudo bash ./script #(and options)

Options:

-i - install all required packages

-j NETWORK_ID - join zerotier network with specified id

-u - make network channel up

-d - make network channel down



(So, at the very first time you need:

sudo bash ./script -i -j <network-id> -u

Later you can just do with -u)

To connect by ssh you need to look on the device mapped address on your network in zerotier and connect to it by:

ssh username@mapped-address

In case of problems with option -j or with zerotier at all:

sudo systemctl restart zerotier-one
