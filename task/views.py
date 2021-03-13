from django.shortcuts import render
from task.models import Entry, Status, Allocation, Vlan
from django.shortcuts import redirect, get_object_or_404
from django.conf import settings
import string
import random

import json
from django.core import serializers

from .orc import Orc
from .vyos import Vyos

def index(request):
    entries = Entry.objects.all()
    return render(request, 'task/index.html', {'entries': entries})

def new_entry(request):
    if request.method == 'POST':
        data = request.POST

        vm_name = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
        username = data.get('username').lower()
        password = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))
        ssh_port = Allocation.get_next_port()
        entry = Entry.objects.create(username=username, entry_type=data.get('task_type'))

        vlan_id = Vlan.get_next_id()
        vlan = Vlan(entry_id=entry.id, vlan_id=vlan_id)
        vlan.save()

        orc = Orc()
        vm = orc.create_vm(vm_name, username, password, ssh_port, vlan_id)
        entry.orc_vm_id = vm['id']
        entry.orc_vm_username = username
        entry.orc_vm_password = password
        entry.orc_vm_fqdn = vm['fqdn']
        entry.public_ipv4 = settings.PUBLIC_IPV4
        entry.public_ipv6 = vm['config']['net']['ipv6']['ip']
        entry.save()

        vyos_rule_id = Allocation.get_next_vyos_rule_id()

        allocation = Allocation(entry_id=entry.id, vyos_rule_id=vyos_rule_id, port=ssh_port, type="ssh")
        allocation.save()

        destination = {
            "address": entry.public_ipv4,
            "port": ssh_port
        }

        translation = {
            "address": vm['config']['net']['ipv4']['ip'],
            "port": ssh_port
        }

        allocation.vyos.create_nat_rule(vyos_rule_id, destination, translation, "Techo - VM: {}".format(vm['id']))

        status = Status(entry_id=entry.id)
        status.save()

        return redirect("/{}".format(entry.id))
    return render(request, 'task/new.html', {'types': Entry.Type.choices})

def delete_entry(request, entry_id):
    entry = get_object_or_404(Entry, pk=entry_id)
    orc = Orc()
    orc.delete_vm(entry.orc_vm_id)

    vyos = Vyos()
    allocations = Allocation.objects.filter(entry_id=entry_id)
    print(allocations)
    for a in allocations:
        if vyos.delete_nat_rule(a.vyos_rule_id):
            a.delete()

    entry.delete()
    return redirect("/")

def entry(request, entry_id):
    entry = get_object_or_404(Entry, pk=entry_id)
    serialized_obj = serializers.serialize('json', [ entry, ])
    return render(request, 'task/show.html', {'entry': entry, 'entry_json': serialized_obj})
