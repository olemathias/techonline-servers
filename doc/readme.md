# 1 INTRO
## 1.1 The task at hand
The task is simple: Get our client an IP using DHCP and respond to DNS requests.

Your job is to configure the DHCP and DNS server.

## 1.2 End result
This is what being checked for:
1.  DHCP - Lease Received and valid.
2.  DNS - Respond to recursion request.
3.  DNS - Recursion not avaliable outside of own subnet.
4.  DNS - Authoritative zone valid.
5.  DNS - Authoritative zone avaliable outside.

## 1.3 Environment
You need an SSH client, if you are on windows "PuTTy" is recommended.

You will be provided an IP address, port, username and password to SSH to, this is where you will work.

Start by making sure that works.

The server you are conneting to have 2 interfaces: eth0 and ens19. eth0 is only used for management traffic and can mostly be ignored. ens19 is the interface that will have a client ready for DHCP.

In a production setup you would generaly never do this, needing to have a dhcp server interface in each subnet does not scale very well. For bigger networks, DHCP relay is almost always used
For this lab it's fine and simpler to configure and understand.

# 2 Reference documentation
## 2.1 Topology

## 2.2 Pre-configured
For convenience, the following is set up:
1. The server is installed with Debian 10, the management network (eth0) is configued and listening on ssh.
2. IP address for ens19 is already configured (10.XX.XX.2).
3. A local user is already configured. Username and password will be provided in our portal. You are free to add other users, change the password and/or add a ssh-key.
4. Get the ip address for ens19 with `ifconfig ens19 | grep inet | grep netmask`


## 2.8 IP-plan
All instances will automaticly be allocated an /24 IPv4 network for the task. See the `ens19` interface for what subnet you got. IPv6 is not needed for this task.

IPv4: For management the server is placed in 10.129.1.0/24 and all traffic to and from the server is NAT'ed behind 185.80.182.120. Only SSH traffic on allocated port is allowed in.
IPv6: You will get a public IPv6 address.  
Filtering: We do filtering on traffic to prevent abuse, let us know if you think this is stopping you from completing the task.

# 2 Tips and tricks
## 3.1 DHCP
There are many DHCP servers out there, the most known are probably isc-dhcp-server. For this task we recommend isc-dhcp-server, but you can choose whatevery you like. The rest of the documentation will assume you are using isc-dhcp-server.  

The server can be installed using apt-get on Debian.  
`apt install isc-dhcp-server`

A few notes:
- The default setup from Debian have the same service for DHCPv4 and DHCPv6, since we are only going to use IPv4 in this lab, it can save you some headache by disabling DHCPv6. Do that by commenting out `INTERFACESv6` (add # to front of the line) in `/etc/default/isc-dhcp-server`.
- While you are in `/etc/default/isc-dhcp-server` add ens19 to `INTERFACESv4`. This tells the server to only listen to ens19.
- The default configuration (/etc/dhcp/dhcpd.conf) have everything you need to complete the task, you will just need to put it together. Read the examples
- The log /var/log/syslog is a good start when something is not working.

Options you will need:
- domain-name (use the one provided)
- domain-name-servers (this must be the server, the ip at ens19)
- default-lease-time
- max-lease-time
- authoritative
- subnet
  - routers

You are free to configure other options if you would like.

## 3.2 DNS
First it can be useful to know the difference between a Recursor and Authoritative nameserver.  
All DNS servers fall into one of four categories: Recursive resolvers, root nameservers, TLD nameservers, and authoritative nameservers. For this task we will focus on recursive resolvers and authoritative nameservers.

A recursive resolver (also known as a DNS recursor) is the first stop in a DNS query. The recursive resolver acts as a middleman between a client and a DNS nameserver. After receiving a DNS query from a client, a recursive resolver will either respond with cached data, or send a request to a root nameserver, followed by another request to a TLD (.no/.org/...) nameserver, and then one last request to an authoritative nameserver. After receiving a response from the authoritative nameserver containing the requested IP address, the recursive resolver then sends a response to the client.  

When a recursive resolver receives a response from a TLD nameserver, that response will direct the resolver to an authoritative nameserver. The authoritative nameserver is usually the resolver’s last step in the journey for an IP address.  
The authoritative nameserver contains information specific to the domain name it serves (e.g. gathering.org) and it can provide a recursive resolver with the IP address of that server found in the DNS A/AAAA record, or if the domain has a CNAME record (alias) it will provide the recursive resolver with an alias domain, at which point the recursive resolver will have to perform a whole new DNS lookup to procure a record from an authoritative nameserver (often an A/AAAA record containing an IP address).  

See more at https://www.cloudflare.com/learning/dns/dns-server-types/

## 3.3 DNS software
As with DHCP, there are multiple options avaliable. The most popular in the latter decades is BIND.

For this task we recommend BIND9, but you can choose whatevery you like. The rest of the documentation will assume you are using bind. Note that we will run the recursor and authoritative on the same IP. This can be an issue with PowerDNS.

Bind9 can be installed using apt-get on Debian.  
`apt install bind9`

## 3.4 Bind
- The config files for bind can be found in /etc/bind/
- To show the current status of bind: `systemctl status bind9`
- After making changes to the config you will need to restart bind9
- You can validate the config with `named-checkconf /etc/bind/named.conf`
- The log /var/log/syslog is a good start when something is not working.

## 3.5 Recursive resolver
- The file named.conf.options is a good start
- Create a ACL for the client subnet
- Enable recursion

### ACL
The ACL should be placed outside of `options {`  
```
acl my_net {
    10.0.0.0/24;
};
```

### Enable recursion
After you have defined the acl, allow recursion under `options`  
```
recursion yes;
allow-recursion { my_net; };
```

## 3.6 Authoritative Nameserver
- Create a zone file for the assigned zone
- The file /etc/bind/named.conf.local is a good start

### zone-XXX.techo.no
In `/etc/bind/named.conf.local` add
```
zone "zone-XXX.techo.no" {
    type master;
    file "/etc/bind/zones/zone-XXX.techo.no"; # zone file path
};
```  

Create a folder to place zone files:  
```
mkdir /etc/bind/zones
```

Example zone - Update to your need:  
```
$TTL    604800
@       IN      SOA     ns1.zone-XXX.techo.no. you.zone-XXX.techo.no. (
         2021040101     ; Serial
             604800     ; Refresh
              86400     ; Retry
            2419200     ; Expire
             604800 )   ; Negative Cache TTL
;
; name servers - NS records
     IN      NS      ns1.zone-XXX.techo.no.

; name servers - A records
ns1.zone-XXX.techo.no.          IN      A       10.128.10.2 ;
```
ns1.zone-XXX.techo.no. is your nameserver, so the server you are working on.

## 3.7 Extra tasks (optinal)
1. Try to create a reverse zone for the assigned subnet. (in-addr.arpa)
2. Make DHCP automaticly create DNS records for it's clients. (Dynamic DNS)
3. Feel free to create more zones.

# TODO notes
- editor (nano guide)
- tcpdump
- dhcp authoritative option
- recursor and authoritative on the same IP/server: why not.
- Write about the DHCP Options (default-lease-time, max-lease-time)
- The diffrent DNS records (A, AAAA, CNAME, NS, SOA, MX, ++)
- @    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
- dig (bind9utils)
- sudo

https://www.digitalocean.com/community/tutorials/how-to-configure-bind-as-a-private-network-dns-server-on-ubuntu-14-04
