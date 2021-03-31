import dhcppython
from pyroute2 import NDB
from pyroute2.common import uifname

from netaddr import *

def get_dhcp(interface, entry):
    vlan_id = entry["vlan_id"]
    try:
        client = dhcppython.client.DHCPClient(interface=str(interface["ifname"]))
        lease = client.get_lease(mac_addr="de:ad:be:ef:c0:de", broadcast=True, relay=None, server="255.255.255.255", options_list=None)
        options = {}
        for option in lease.ack.options:
            option_name = type(option).__name__
            if option_name in ["ServerIdentifier", "IPAddressLeaseTime", "SubnetMask", "Router", "DNSServer", "DomainName"]:
                options.update({str(option_name): {"name": str(option_name), "code": str(option.code), "value": option.value[next(iter(option.value))]}})
        server = str(lease.server[0])
        if lease.ack.ciaddr is not None:
            interface.add_ip(str(lease.ack.ciaddr)+"/24").set('state', 'up').commit()
        return {"ip": str(lease.ack.ciaddr), "options": options, "server": server}

    except dhcppython.exceptions.DHCPClientError as e:
        return False

    except Exception as e:
        print(e)
        return False

# Test tests

# 1.  DHCP - Received
def check_dhcp_received(dhcp_info, entry, skip=False):
    status = False
    if skip is False:
        if dhcp_info is not False and "ip" in dhcp_info:
            status = True

    return {
        "task_shortname": "dhcp",
        "shortname": "dhcp_received",
        "name": "DHCP Message Received",
        "description": "Check if DHCP message is received",
        "sequence": 1,
        "status_success": status,
        "status_description": "We got a message!" if status else "Skipped" if skip else "Timeout..."
     }

# 2.  DHCP - Correct subnet mask
def check_dhcp_subnet_mask(dhcp_info, entry, skip=False):
    status = False
    if skip is False:
        if "SubnetMask" in dhcp_info["options"] and dhcp_info["options"]["SubnetMask"]["value"] == "255.255.255.0":
            status = True

    return {
        "task_shortname": "dhcp",
        "shortname": "dhcp_subnet_mask",
        "name": "DHCP Subnet Mask",
        "description": "Check received subnet mask is a /24",
        "sequence": 2,
        "status_success": status,
        "status_description": "LGTM!" if status else "Skipped - No DHCP message" if skip else "Got {}, excepted {}".format(dhcp_info["options"]["SubnetMask"]["value"], "255.255.255.0")
     }

# 3.  DHCP - Correct subnet
def check_dhcp_subnet(dhcp_info, entry, skip=False):
    status = False
    if skip is False:
        subnet = IPNetwork(entry["vlan_ip"])
        ip = IPNetwork(dhcp_info["ip"]+"/24")
        if subnet == ip:
            status = True
    return {
        "task_shortname": "dhcp",
        "shortname": "dhcp_subnet",
        "name": "DHCP Subnet",
        "description": "Check if assigned IP is in correct subnet",
        "sequence": 3,
        "status_success": status,
        "status_description": "LGTM!" if status else "Skipped - No DHCP message" if skip else "Got {}, excepted {}".format(str(ip), str(subnet))
     }

# 4.  DHCP - Correct gateway
def check_dhcp_gateway(dhcp_info, entry, skip=False):
    status = False
    if skip is False:
        status_description = "Missing Router option?"
        if "Router" in dhcp_info["options"] and len(dhcp_info["options"]["Router"]["value"]) >= 1:
            subnet = IPNetwork(dhcp_info["ip"]+"/24")
            gateway = str(subnet[1])
            if gateway == dhcp_info["options"]["Router"]["value"][0]:
                status = True
            status_description = "LGTM!" if status else "Got {}, excepted {}".format(str(dhcp_info["options"]["Router"]["value"][0]), str(gateway))
    return {
        "task_shortname": "dhcp",
        "shortname": "dhcp_gateway",
        "name": "DHCP Router",
        "description": "Check if assigned Router is in correct subnet",
        "sequence": 4,
        "status_success": status,
        "status_description": status_description if skip is False else "Skipped - No DHCP message"
     }

# 5.  DHCP - DNS Servers provided
def check_dhcp_dns(dhcp_info, entry, skip=False):
    status = False
    if skip is False:
        status_description = "Missing DNSServer?"
        if "DNSServer" in dhcp_info["options"] and len(dhcp_info["options"]["DNSServer"]["value"]) >= 1:
            if dhcp_info["options"]["DNSServer"]["value"][0] == str(IPNetwork(entry["vlan_ip"]).ip):
                status = True
            status_description = "LGTM!" if status else "Got {}, excepted {}".format(str(dhcp_info["options"]["DNSServer"]["value"][0]), str(IPNetwork(entry["vlan_ip"]).ip))
    return {
        "task_shortname": "dhcp",
        "shortname": "dhcp_dns",
        "name": "DHCP DNS Option",
        "description": "Check if we received a DNSServer option",
        "sequence": 5,
        "status_success": status,
        "status_description": status_description if skip is False else "Skipped - No DHCP message"
     }

# 6.  DHCP - DomainName provided
def check_dhcp_domain_name(dhcp_info, entry, skip=False):
    status = False
    if skip is False:
        if "DomainName" in dhcp_info["options"]:
            status_description = "Missing DomainName option?"
            if dhcp_info["options"]["DomainName"]['value'] == entry["zone"]:
                status = True
            status_description = "LGTM!" if status else "Skipped" if skip else "Got {}, excepted {}".format(str(dhcp_info["options"]["DomainName"]['value']), str(entry["zone"]))
    return {
        "task_shortname": "dhcp",
        "shortname": "dhcp_domain_name",
        "name": "DHCP DomainName Option",
        "description": "Check if we received a DomainName option",
        "sequence": 6,
        "status_success": status,
        "status_description": status_description if skip is False else "Skipped - No DHCP message"
     }
