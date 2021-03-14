# Needs Python 3.8

import dhcppython
from pyroute2 import NDB
from pyroute2.common import uifname

from flask import Flask, jsonify
import os

import jsonpickle

app = Flask(__name__)

ndb = NDB(log='on')

@app.route('/<vlan_id>')
def hello_world(vlan_id):
    return jsonify(check_dhcp(int(vlan_id)))

def check_dhcp(vlan_id):
    interface_name = uifname()

    (ndb.interfaces
    .create(ifname=interface_name, kind='vlan', link='ens19', vlan_id=vlan_id)
    .set('state', 'up')
    .commit())

    try:
        client = dhcppython.client.DHCPClient(interface=str(interface_name))
        lease = client.get_lease(mac_addr="de:ad:be:ef:c0:de", broadcast=True, relay=None, server="255.255.255.255", options_list=None)
        ndb.interfaces[interface_name].remove().commit()
        print(lease)
        options = []
        for option in lease.ack.options:
            option_name = type(option).__name__
            if option_name in ["ServerIdentifier", "IPAddressLeaseTime", "SubnetMask", "Router", "DNSServer", "DomainName"]:
                options.append({"name": str(option_name),"code": str(option.code), "data": str(option.data)})
        server = str(lease.server[0])
        return {"status": "ok", "vlan_id": vlan_id, "ip": str(lease.ack.ciaddr), "options": options, "server": server}

    except dhcppython.exceptions.DHCPClientError as e:
        ndb.interfaces[interface_name].remove().commit()
        return {"status": "failed - timeout", "vlan_id": vlan_id}

if __name__ == '__main__':
    host = os.environ.get('SERVER_HOST', '0.0.0.0')
    port = os.environ.get('SERVER_PORT', 8010)
    debug = os.getenv("DEBUG", 'True').lower() in ['true', '1']
    app.run(debug=debug, host=host, port=port)
