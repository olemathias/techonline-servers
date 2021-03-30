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


r = requests.get('http://10.10.150.5:9090/api/entries/1', auth=('tgo', 'tech21'))
entries = r.json()

for e in entries:

    r = requests.get('http://10.10.150.5:9090/api/entry/{}'.format(e['id']), auth=('tgo', 'tech21'))
    entry = r.json()

    # Loop here fetch entries from api
    print("Running test for {} (vlan_id: {})".format(entry["fqdn"], entry["vlan_id"]))

    interface_name = uifname()

    interface = setup_interface(interface_name, entry['vlan_id'])
    dhcp_info = get_dhcp(interface, entry)

    status = []

    try:
        status.append(make_full_test(check_dhcp_received(dhcp_info, entry), entry))

        if check_dhcp_received(dhcp_info, entry)['status_success'] is True:
            status.append(make_full_test(check_dhcp_subnet_mask(dhcp_info, entry), entry))
            status.append(make_full_test(check_dhcp_subnet(dhcp_info, entry),entry))
            status.append(make_full_test(check_dhcp_gateway(dhcp_info, entry),entry))
            status.append(make_full_test(check_dhcp_dns(dhcp_info, entry),entry))
            status.append(make_full_test(check_dhcp_domain_name(dhcp_info, entry),entry))

            if check_dhcp_dns(dhcp_info, entry)['status_success'] is True:
                server = dhcp_info["options"]["DNSServer"]["value"][0]
                status.append(make_full_test(check_dns_rec(server, entry),entry))

    except Exception as e:
        print(e)
        pass

    cleanup_interface(interface)

    print(json.dumps(status, indent=4, sort_keys=True))
