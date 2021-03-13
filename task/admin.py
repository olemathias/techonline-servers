from django.contrib import admin

from .models import Entry, Status, Allocation, Vlan

# Register your models here.
admin.site.register(Entry)
admin.site.register(Status)
admin.site.register(Allocation)
admin.site.register(Vlan)
