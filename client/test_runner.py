#!/usr/bin/env python

# Needs Python 3.8

import dhcppython
from pyroute2 import NDB
from pyroute2.common import uifname
import os
import random

import requests

import json

from dhcp_test import *
from dns_test import *

f=open("./backend.txt","r")
lines=f.readlines()
backend_url=lines[0].rstrip("\n")
backend_username=lines[1].rstrip("\n")
backend_password=lines[2].rstrip("\n")
f.close()

f=open("./techonline-servers.txt","r")
lines=f.readlines()
tos_url=lines[0].rstrip("\n")
tos_username=lines[1].rstrip("\n")
tos_password=lines[2].rstrip("\n")
f.close()

ndb = NDB(log='on')

def setup_interface(interface_name, vlan_id):
    interface = (ndb.interfaces
    .create(ifname=interface_name, kind='vlan', link='ens19', vlan_id=vlan_id)
    .set('state', 'up')
    .commit())
    return interface

def cleanup_interface(interface):
    try:
        interface.remove().commit()
        return True
    except Exception as e:
        print(e)
        return False

def make_full_test(msg, entry):
    msg.update({"track": "server", "station_shortname": str(entry["id"])})
    return msg

stations = requests.get('{}/api/stations/?track=server'.format(backend_url), auth=(backend_username, backend_password)).json()

for station in stations:
    if station["status"] in ["terminated"]:
        continue

    print(station["name"])

    r = requests.get('{}/api/entry/{}'.format(tos_url, int(station['shortname'])), auth=(tos_username, tos_password))
    entry = r.json()

    # Loop here fetch entries from api
    print("Running test for {} (vlan_id: {})".format(entry["fqdn"], entry["vlan_id"]))

    interface_name = uifname()

    interface = setup_interface(interface_name, entry['vlan_id'])
    dhcp_info = get_dhcp(interface, entry)

    status = []

    try:
        status.append(make_full_test(check_dhcp_received(dhcp_info, entry), entry))

        skip = check_dhcp_received(dhcp_info, entry)['status_success'] is False
        status.append(make_full_test(check_dhcp_subnet_mask(dhcp_info, entry, skip), entry))
        status.append(make_full_test(check_dhcp_subnet(dhcp_info, entry, skip),entry))
        status.append(make_full_test(check_dhcp_gateway(dhcp_info, entry, skip),entry))
        status.append(make_full_test(check_dhcp_dns(dhcp_info, entry, skip),entry))
        status.append(make_full_test(check_dhcp_domain_name(dhcp_info, entry, skip),entry))

        skip = check_dhcp_dns(dhcp_info, entry, skip)['status_success'] is False
        server = ""
        if skip is False:
            server = dhcp_info["options"]["DNSServer"]["value"][0]

        status.append(make_full_test(check_dns_rec(server, entry, skip),entry))
        status.append(make_full_test(check_dns_auth_soa(server, entry, skip),entry))

    except Exception as e:
        print(e)
        pass

    cleanup_interface(interface)

    for x in status:
        r = requests.post('{}/api/test/'.format(backend_url), auth=(backend_username, backend_password), json=x)
        if r.status_code != 201:
            print("Failed to push status, got {}".format(r.status_code))

    print(json.dumps(status, indent=4, sort_keys=True))

ndb.close()
