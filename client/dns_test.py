import dns.message
import dns.query

import random

def make_dns_request(type, server, domain):
    try:
        q = dns.message.make_query(domain, type.upper())
        dns.query.tcp(q, server).to_text()
        return True

    except ConnectionRefusedError as e:
        return False

    except Exception as e:
        print(e)
        return False

def check_dns_rec(server, entry):
    status = False
    domains = ["gathering.org", "vg.no", "nrk.no",
    "google.com", "facebook.com", "mozilla.org", "microsoft.com",
    "tiktok.com", "techo.gathering.org", "tech.gathering.org", "bbc.co.uk",
    "nextron.no", "nexthop.no", "gathering.systems", "juniper.net"]

    # Try 2 times
    if make_dns_request("a", server, random.choice(domains)) or make_dns_request("a", server, random.choice(domains)):
        status = True
    return {
        "task_shortname": "dns_rec",
        "shortname": "dns_rec",
        "name": "DNS Recursor",
        "description": "Check if DNS Recursor works",
        "sequence": 11,
        "status_success": status,
        "status_description": "LGTM!" if status else "Timeout?"
     }
