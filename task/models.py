from django.db import models
from django.conf import settings
from task.orc import Orc
from task.vyos import Vyos

import string
import random

EntryType = ["dhcp-dns"]

class Entry(models.Model):
    class Type(models.IntegerChoices):
        DHCP_DNS = 1
        GONDUL = 2
    entry_type = models.PositiveSmallIntegerField(choices=Type.choices)
    username = models.CharField(max_length=256)
    orc_vm_id = models.CharField(max_length=256, default=None, null=True)
    orc_vm_username = models.CharField(max_length=64, default=None, null=True)
    orc_vm_password = models.CharField(max_length=64, default=None, null=True)
    orc_vm_fqdn = models.CharField(max_length=64, default=None, null=True)
    public_ipv4 = models.GenericIPAddressField(default=None, null=True)
    public_ipv6 = models.GenericIPAddressField(default=None, null=True)
    vlan_id = models.PositiveIntegerField(default=None, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    orc_vm = None

    @classmethod
    def get_next_vlan_id(self):
        vlans = Entry.objects.all().values_list('vlan_id', flat=True)
        for i in list(range(1050, 1200)):
            if i not in vlans:
                return i

    @classmethod
    def new(self, ssh_username, uid, entry_type):
        vm_name = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
        username = ssh_username.lower()
        password = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))
        ssh_port = Allocation.get_next_port()


        entry = Entry.objects.create(username=uid, entry_type=entry_type)
        entry.orc_vm_username = username
        entry.orc_vm_password = password
        entry.public_ipv4 = settings.PUBLIC_IPV4
        entry.save()

        ssh_vyos_rule_id = Allocation.get_next_vyos_rule_id()
        ssh_allocation = Allocation(entry_id=entry.id, vyos_rule_id=ssh_vyos_rule_id, port=ssh_port, type="ssh")
        ssh_allocation.save()

        vlan_id = None

        # DHCP DNS
        if entry_type == 1:
            vlan_id = Entry.get_next_vlan_id()
            entry.vlan_id = vlan_id

        orc = Orc()
        vm = orc.create_vm(vm_name, username, password, ssh_port, vlan_id)
        entry.orc_vm_id = vm['id']
        entry.orc_vm_fqdn = vm['fqdn']
        entry.public_ipv6 = vm['config']['net']['ipv6']['ip']
        entry.save()

        ssh_destination = {
            "address": entry.public_ipv4,
            "port": ssh_port
        }
        ssh_translation = {
            "address": vm['config']['net']['ipv4']['ip'],
            "port": ssh_port
        }
        ssh_allocation.vyos.create_nat_rule(ssh_vyos_rule_id, ssh_destination, ssh_translation, "Techo - VM: {}".format(vm['id']))

        status = Status(entry_id=entry.id)
        status.save()

        return entry

    @property
    def allocations(self):
        return Allocation.objects.filter(entry_id=self.id)

    @property
    def vm(self):
        if self.orc_vm is None:
            orc = Orc()
            self.orc_vm = orc.get_vm(self.orc_vm_id)
        return self.orc_vm

    def status(self):
        return Status.objects.get(entry=self)

class Allocation(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    vyos_rule_id = models.PositiveIntegerField(default=None, null=True)
    port = models.PositiveIntegerField(default=None, null=True)
    type = models.CharField(max_length=256, default=None, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    vyos_obj = None

    @property
    def vyos(self):
        if self.vyos_obj is None:
            self.vyos_obj = Vyos()
        return self.vyos_obj

    @classmethod
    def get_next_vyos_rule_id(self):
        allocations = Allocation.objects.all().values_list('vyos_rule_id', flat=True)
        for i in list(range(1100, 1200)):
            if i not in allocations:
                return i

    @classmethod
    def get_next_port(self):
        ports = Allocation.objects.all().values_list('port', flat=True)
        for i in list(range(20001, 20200)):
            if i not in ports:
                return i

class Status(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    status = models.JSONField(default=None, null=True)
    updated = models.DateTimeField(auto_now=True)
