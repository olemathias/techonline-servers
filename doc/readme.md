# 1 INTRO
## 1.1 The task at hand
The task is simple: Get our client an IP using DHCP and respond to DNS requests.

Your job is to configure the DHCP and DNS server.

## 1.2 End result
This is what being checked for:
1.  DHCP - Lease Received and valid
2.  DNS - Respond to recursion (gathering.org)
3.  DNS - Recursion not avaliable outside of own subnet.
4.  DNS - Authoritative zone valid

## 1.3 Environment
You need an SSH client, if you are on windows "PuTTy" is recommended.

You will be provided an IP address, port, username and password to SSH to, this is where you will work.

Start by making sure that works.

The server you are conneting to have 2 interfaces: eth0 and ens19. eth0 is only used for management traffic and can mostly be ignored. ens19 is the interface that will have a client ready for DHCP.

In a production setup you would generaly never do this, having a server interface in each subnet does not scale very well. For bigger networks, DHCP relay is often used. TODO write more  
But for this small lab it's fine and a little simpler to setup and understand.

# 2 Reference documentation
## 2.1 Topology

## 2.2 Pre-configured
For convenience, the following is set up:
1. The server is installed with Debian 10, the management network (eth0) is configued and listening on ssh.
2. IP address for ens19 is already configured.

## 2.7 Credentials
1. SSH to the provided IP using the provided username and password.

## 2.8 IP-plan
All instances will automaticly be allocated an /24 network for the task. See the ens19 interface for what range will use.

# 2 Tips and tricks
## 3.1 DHCP
There are many DHCP servers out there, the most known are probaly isc-dhcp-server and kea-dhcp-server. For this task we recommend isc-dhcp-server, but you can choose whatevery you like. The rest of the documentation will assume you are using isc-dhcp-server

The server can be installed using apt-get on Debian.  
`apt install isc-dhcp-server`

A few notes:
- The default setup from Debian have the same service for DHCPv4 and DHCPv6, since we are only going to use v4 in this lab, it can save you some headiche by disabling DHCPv6. Do that by commenting out INTERFACESv6 (add # to front of the line) in /etc/default/isc-dhcp-server # TODO check this
- While you are in /etc/default/isc-dhcp-server add ens19 to INTERFACESv4. This tells the server to only listen to ens19. (the interface with clients)
- The default configuration (/etc/dhcp/dhcpd.conf) have everything you need to complete the task, you will just need to put it together.
- The log /var/log/syslog is generaly a good start when something is not working.

Options you will need:
- domain-name (use the one provided)
- domain-name-servers (this must be your own server, the ip at ens19)
- default-lease-time
- max-lease-time
- authoritative
- subnet
  - routers

You are free to configure other options if you would like.

## 3.2 DNS
First it can be usefull to know the dirrfrenct between a Recursor and Authoritative nameserver. All DNS servers fall into one of four categories: Recursive resolvers, root nameservers, TLD nameservers, and authoritative nameservers.

A recursive resolver (also known as a DNS recursor) is the first stop in a DNS query. The recursive resolver acts as a middleman between a client and a DNS nameserver. After receiving a DNS query from a web client, a recursive resolver will either respond with cached data, or send a request to a root nameserver, followed by another request to a TLD nameserver, and then one last request to an authoritative nameserver. After receiving a response from the authoritative nameserver containing the requested IP address, the recursive resolver then sends a response to the client.


When a recursive resolver receives a response from a TLD nameserver, that response will direct the resolver to an authoritative nameserver. The authoritative nameserver is usually the resolver’s last step in the journey for an IP address.  
The authoritative nameserver contains information specific to the domain name it serves (e.g. gathering.org) and it can provide a recursive resolver with the IP address of that server found in the DNS A/AAAA record, or if the domain has a CNAME record (alias) it will provide the recursive resolver with an alias domain, at which point the recursive resolver will have to perform a whole new DNS lookup to procure a record from an authoritative nameserver (often an A/AAAA record containing an IP address).

See more at https://www.cloudflare.com/learning/dns/dns-server-types/

## 3.3 DNS recursor
As with DHCP, there are multiple options avaliable. The most popular over the decades is BIND.

For this task we recommend BIND9, but you can choose whatevery you like. The rest of the documentation will assume you are using bind. Note that we will run the recursor and authoritative on the same IP.

Bind9 can be installed using apt-get on Debian.  
`apt install bind9`

# TODO notes
- editor (nano guide)
- tcpdump
- dhcp authoritative
- recursor and authoritative on the same IP: why not.
- Write about the DHCP Options (default-lease-time, max-lease-time)
