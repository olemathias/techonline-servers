#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'techo_srv.settings')
django.setup()

# write your code here
import time
from task.models import Task, Status

import subprocess
import re
import requests

def ping(ip):
    args=['/sbin/ping', '-c', '3', '-W', '1', str(ip)]
    p_ping = subprocess.Popen(args,
                              shell=False,
                              stdout=subprocess.PIPE)
    # save ping stdout
    p_ping_out = str(p_ping.communicate()[0])

    #print(p_ping_out)

    if (p_ping.wait() == 0):
      # rtt min/avg/max/mdev = 22.293/22.293/22.293/0.000 ms
      search = re.search(r'(.*)/(.*)/(.*)/(.*) ms',
                         p_ping_out, re.M|re.I)
      ping_rtt = search.group(2)
      print("OK " + str(ip) + " rtt= "+ ping_rtt)
      return True
    return False

def http_check(url):
    try:
        r = requests.get(url, timeout=0.5)
        if r.status_code >= 200 < 300:
            return True
    except requests.exceptions.ConnectionError:
        return False

running = True
while running:
    for entry in Task.objects.all():
        stat = {}
        stat.update({'ipv4_ping': ping(entry.public_ipv4)})
        stat.update({'ipv6_ping': ping(entry.public_ipv6)})
        stat.update({'http': http_check("http://{}".format(entry.public_ipv4))})
        print(stat)
        Status.objects.filter(task_id=entry.id).update(status=stat)
    time.sleep(5)
