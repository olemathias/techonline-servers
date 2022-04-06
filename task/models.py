from django.db import models
from django.conf import settings
from task.orc import Orc
# from task.vyos import Vyos
from task.pdns import PowerDNS

import string
import random

class Entry(models.Model):
    class Type(models.IntegerChoices):
        DHCP_DNS = 1
        GONDUL = 2
    entry_type = models.PositiveSmallIntegerField(choices=Type.choices)
    username = models.CharField(max_length=256)
    orc_vm_id = models.CharField(max_length=256, default=None, null=True)
    orc_vm_username = models.CharField(max_length=64, default=None, null=True)
    orc_vm_password = models.CharField(max_length=64, default=None, null=True)
    orc_vm_fqdn = models.CharField(max_length=128, default=None, null=True)
    public_ipv4 = models.GenericIPAddressField(default=None, null=True)
    public_ipv6 = models.GenericIPAddressField(default=None, null=True)
    zone_fqdn = models.CharField(max_length=128, default=None, null=True)
    fqdn = models.CharField(max_length=128, default=None, null=True)
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

    def dump(self):
        return {
            "id": self.id,
            "entry_type": self.entry_type,
            "uid": self.username,
            "orc_vm_id": self.orc_vm_id,
            "orc_vm_username": self.orc_vm_username,
            "orc_vm_password": self.orc_vm_password,
            "orc_vm_fqdn": self.orc_vm_fqdn,
            "public_ipv4": self.public_ipv4,
            "public_ipv6": self.public_ipv6,
            "ssh_port": self.allocations[0].port,
            "fqdn": self.fqdn[:-1],
            "zone": self.zone_fqdn[:-1],
            "vlan_id": self.vlan_id,
            "vlan_ip": "10.{}.{}.2/24".format(str(self.vlan_id)[:2], str(self.vlan_id)[-2:]),
            "mgmt_ipv4": self.vm['config']['net']['ipv4']['ip'],
            "created_at": self.created,
            "updated_at": self.updated
        }

    def cleanup(self):
        orc = Orc()
        orc.delete_vm(self.orc_vm_id)

        # vyos = Vyos()
        # allocations = Allocation.objects.filter(entry_id=self.id)
        # for a in allocations:
        #     if vyos.delete_nat_rule(a.vyos_rule_id):
        #         a.delete()

        rrsets = []
        if self.fqdn is not None:
            rrsets.append({
                "name": self.fqdn,
                "changetype": "delete",
                "type": "A",
                "records": [{
                    "content": self.public_ipv4,
                    "disabled": False,
                    "type": "A"
                }],
                "ttl": 60
            })
            rrsets.append({
                "name": self.fqdn,
                "changetype": "delete",
                "type": "AAAA",
                "records": [{
                    "content": self.public_ipv6,
                    "disabled": False,
                    "type": "AAAA"
                }],
                "ttl": 60
            })

        if self.zone_fqdn is not None:
            rrsets.append({
                "name": self.zone_fqdn,
                "changetype": "delete",
                "type": "NS",
                "records": [{
                    "content": self.fqdn,
                    "disabled": False,
                    "type": "NS"
                }],
                "ttl": 60
            })
            #console = Console(host="10.10.150.8",
            #                  port=5199,
            #                  key="")
            #o = console.send_command(cmd="rmServer({{address=\"{}\", pool=\"{}\"}})".format(vm['config']['net']['ipv4']['ip'], vm_name))
            #print(o)
            #o = console.send_command(cmd="rmRule({{'{}'}})".format(vm_name))
            #print(o)

        if len(rrsets) >= 1:
            pdns = PowerDNS(settings.PDNS_API_URL, settings.PDNS_API_KEY)
            pdns.set_records(settings.BASE_DOMAIN+".", rrsets)

        self.delete()

    @classmethod
    def new(self, ssh_username, uid, entry_type):
        vm_name = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
        username = ssh_username.lower()
        password = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))
        ssh_port = Allocation.get_next_port()


        entry = Entry.objects.create(username=uid, entry_type=entry_type)
        entry.orc_vm_username = username
        entry.orc_vm_password = password
        # entry.public_ipv4 = settings.PUBLIC_IPV4
        entry.save()

        # ssh_vyos_rule_id = Allocation.get_next_vyos_rule_id()
        # ssh_allocation = Allocation(entry_id=entry.id, vyos_rule_id=ssh_vyos_rule_id, port=ssh_port, type="ssh")
        # ssh_allocation.save()

        entry.fqdn = "vm-{}.{}.".format(vm_name, settings.BASE_DOMAIN)
        rrsets = []

        vlan_id = None
        # DHCP DNS
        if int(entry_type) == 1:
            vlan_id = Entry.get_next_vlan_id()
            entry.vlan_id = vlan_id
            entry.zone_fqdn = "zone-{}.{}.".format(vm_name, settings.BASE_DOMAIN)
            rrsets.append({
                "name": entry.zone_fqdn,
                "changetype": "replace",
                "type": "NS",
                "records": [{
                    "content": entry.fqdn,
                    "disabled": False,
                    "type": "NS"
                }],
                "ttl": 60
            })

        orc = Orc()
        vm = orc.create_vm(vm_name, username, password, ssh_port, vlan_id)
        entry.orc_vm_id = vm['id']
        entry.orc_vm_fqdn = vm['fqdn']
        entry.public_ipv4 = vm['config']['net']['ipv4']['ip']
        entry.public_ipv6 = vm['config']['net']['ipv6']['ip']
        entry.save()

        # ssh_destination = {
        #     "address": entry.public_ipv4,
        #     "port": ssh_port
        # }
        # ssh_translation = {
        #     "address": vm['config']['net']['ipv4']['ip'],
        #     "port": ssh_port
        # }
        # ssh_allocation.vyos.create_nat_rule(ssh_vyos_rule_id, ssh_destination, ssh_translation, "Techo - VM: {}".format(vm['id']))

        rrsets.append({
            "name": entry.fqdn,
            "changetype": "replace",
            "type": "A",
            "records": [{
                "content": entry.public_ipv4,
                "disabled": False,
                "type": "A"
            }],
            "ttl": 60
        })
        rrsets.append({
            "name": entry.fqdn,
            "changetype": "replace",
            "type": "AAAA",
            "records": [{
                "content": entry.public_ipv6,
                "disabled": False,
                "type": "AAAA"
            }],
            "ttl": 60
        })

        pdns = PowerDNS(settings.PDNS_API_URL, settings.PDNS_API_KEY)
        pdns.set_records(settings.BASE_DOMAIN+".", rrsets)

        status = Status(entry_id=entry.id)
        status.save()

        # DHCP DNS
        #if int(entry_type) == 1:
        #    console = Console(host="10.10.150.8",
        #                      port=5199,
        #                      key="")
        #    o = console.send_command(cmd="newServer({{address=\"{}\", pool=\"{}\"}})".format(vm['config']['net']['ipv4']['ip'], vm_name))
        #    print(o)
        #    o = console.send_command(cmd="addAction({{'{}'}}, PoolAction(\"{}\"))".format(entry.zone_fqdn, vm_name))
        #    print(o)

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

    # vyos_obj = None

    # @property
    # def vyos(self):
    #     if self.vyos_obj is None:
    #         self.vyos_obj = Vyos()
    #     return self.vyos_obj

    # @classmethod
    # def get_next_vyos_rule_id(self):
    #     allocations = Allocation.objects.all().values_list('vyos_rule_id', flat=True)
    #     for i in list(range(1100, 1200)):
    #         if i not in allocations:
    #             return i

    # @classmethod
    # def get_next_port(self):
    #     ports = Allocation.objects.all().values_list('port', flat=True)
    #     for i in list(range(20001, 20200)):
    #         if i not in ports:
    #             return i

class Status(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    status = models.JSONField(default=None, null=True)
    updated = models.DateTimeField(auto_now=True)
