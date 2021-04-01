import dns.message
import dns.query

import random

def make_dns_request(type, server, domain):
    try:
        q = dns.message.make_query(domain, type.upper())
        return dns.query.tcp(q, server, timeout=2).answer

    except ConnectionRefusedError as e:
        return False

    except Exception as e:
        print(e)
        return False

def check_dns_rec(server, entry, skip=False):
    status = False
    if skip is False:
        domains = ["gathering.org", "vg.no", "nrk.no",
        "google.com", "facebook.com", "mozilla.org", "microsoft.com",
        "tiktok.com", "techo.gathering.org", "tech.gathering.org", "bbc.co.uk",
        "nextron.no", "nexthop.no", "gathering.systems", "juniper.net"]

        test1 = make_dns_request("a", server, random.choice(domains))
        test2 = make_dns_request("a", server, random.choice(domains))

        if test1 or test2 is not False:
            if len(test1) >= 1 or len(test2) >= 1:
                status = True
                status_description = "LGTM!"
            else:
                status_description = "Not found?"
        else:
                status_description = "Timeout?"
    else:
        status_description = "Skipped"
    return {
        "task_shortname": "dns_rec",
        "shortname": "dns_rec",
        "name": "DNS Recursor",
        "description": "Check if DNS Recursor works",
        "sequence": 11,
        "status_success": status,
        "status_description": status_description
     }

# Test outside
def check_dns_rec_outside(server, entry, skip=False):
    status = False
    if skip is False:
        domains = ["gathering.org", "vg.no", "nrk.no",
        "google.com", "facebook.com", "mozilla.org", "microsoft.com",
        "tiktok.com", "techo.gathering.org", "tech.gathering.org", "bbc.co.uk",
        "nextron.no", "nexthop.no", "gathering.systems", "juniper.net"]

        test1 = make_dns_request("a", server, random.choice(domains))
        test2 = make_dns_request("a", server, random.choice(domains))

        if test1 or test2 is False:
            status = True
            status_description = "LGTM!"
        else:
            status_description = "Recursion avaliable outside of local subnet!"
    else:
        status_description = "Skipped"
    return {
        "task_shortname": "dns_rec",
        "shortname": "dns_rec_outside",
        "name": "DNS Recursor Outside",
        "description": "Check if DNS Recursor is avaliable from outside",
        "sequence": 11,
        "status_success": status,
        "status_description": status_description
     }

# Check SOA

def check_dns_auth_soa(server, entry, skip=False):
    status = False
    if skip is False:
        q = make_dns_request("soa", server, entry["zone"])
        if q is not False:
            if len(q) >= 1 and len(q[0]) >= 1:
                x = q[0][0]
                if x.serial is not None and x.rname is not None and x.mname is not None:
                    if str(x.mname) == "ns1."+entry["zone"]+".":
                        status = True
                        status_description = "LGTM!"
                    else:
                        status_description = "Nameserver in SOA is {}, excepted {}".format(str(x.mname), "ns1."+entry["zone"]+".")
                else:
                    status_description = "SOA invalid?"
            else:
                status_description = "SOA not found?"
        else:
            status_description = "Timeout?"
    else:
        status_description = "Skipped"

    return {
        "task_shortname": "dns_auth",
        "shortname": "dns_auth_soa",
        "name": "DNS Authoritative SOA",
        "description": "Check if SOA for {} exists".format(entry["zone"]),
        "sequence": 21,
        "status_success": status,
        "status_description": status_description
     }

# Check NS
def check_dns_auth_ns(server, entry, skip=False):
    status = False
    if skip is False:
        q = make_dns_request("ns", server, entry["zone"])
        if q is not False:
            if len(q) >= 1 and len(q[0]) >= 1:
                x = q[0][0]
                if x.target is not None:
                    if str(x.target) == "ns1."+entry["zone"]+".":
                        status = True
                        status_description = "LGTM!"
                    else:
                        status_description = "NS is {}, excepted {}".format(str(x.mname), "ns1."+entry["zone"]+".")
                else:
                    status_description = "NS invalid?"
            else:
                status_description = "NS not found?"
        else:
            status_description = "Timeout?"
    else:
        status_description = "Skipped"

    return {
        "task_shortname": "dns_auth",
        "shortname": "dns_auth_ns",
        "name": "DNS Authoritative NS",
        "description": "Check if NS for {} exists".format(entry["zone"]),
        "sequence": 22,
        "status_success": status,
        "status_description": status_description
     }

# Check A for NS
def check_dns_auth_ns_a(server, entry, skip=False):
    status = False
    if skip is False:
        q = make_dns_request("a", server, "ns1."+entry["zone"])
        if q is not False:
            if len(q) >= 1 and len(q[0]) >= 1:
                status = True
                status_description = "LGTM!"
            else:
                status_description = "A for {} not found?".format("ns1."+entry["zone"])
        else:
            status_description = "Timeout?"
    else:
        status_description = "Skipped"

    return {
        "task_shortname": "dns_auth",
        "shortname": "dns_auth_ns",
        "name": "DNS Authoritative NS",
        "description": "Check if A record for NS exists",
        "sequence": 23,
        "status_success": status,
        "status_description": status_description
     }
