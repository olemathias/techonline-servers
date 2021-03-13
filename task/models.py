from django.db import models
from task.orc import Orc
from task.vyos import Vyos

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
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    orc_vm = None

    @property
    def allocations(self):
        return Allocation.objects.filter(entry_id=self.id)

    @property
    def vlan(self):
        return Vlan.objects.get(entry_id=self.id)

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

class Vlan(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    vlan_id = models.PositiveIntegerField(default=None, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @classmethod
    def get_next_id(self):
        vlans = Vlan.objects.all().values_list('vlan_id', flat=True)
        for i in list(range(1050, 1200)):
            if i not in vlans:
                return i

class Status(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    status = models.JSONField(default=None, null=True)
    updated = models.DateTimeField(auto_now=True)
