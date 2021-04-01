import dns.message
import dns.query

import random

def make_dns_request(type, server, domain):
    try:
        q = dns.message.make_query(domain, type.upper())
        a = dns.query.tcp(q, server, timeout=2).answer
        if len(a) < 1:
            return False
        return a[0]

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

        # Try 2 times
        if make_dns_request("a", server, random.choice(domains)) is not False or make_dns_request("a", server, random.choice(domains)) is not False:
            status = True
    return {
        "task_shortname": "dns_rec",
        "shortname": "dns_rec",
        "name": "DNS Recursor",
        "description": "Check if DNS Recursor works",
        "sequence": 11,
        "status_success": status,
        "status_description": "LGTM!" if status else "Skipped" if skip else "Timeout?"
     }

def check_dns_auth_soa(server, entry, skip=False):
    status = False
    if skip is False:
        q = make_dns_request("soa", server, entry["zone"])
        if q is not False:
            print(q)
            status = True
    return {
        "task_shortname": "dns_auth",
        "shortname": "dns_auth",
        "name": "DNS Authoritative",
        "description": "Check if SOA for {} exists".format(entry["zone"]),
        "sequence": 21,
        "status_success": status,
        "status_description": "LGTM!" if status else "Skipped" if skip else "Timeout?"
     }
