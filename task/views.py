from django.shortcuts import render
from task.models import Entry, Status, Allocation
from django.shortcuts import redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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
        entry = Entry.new(data.get('username').lower(), data.get('username').lower(), data.get('task_type'))
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

@csrf_exempt
def api_entries(request, type):
    return JsonResponse(list(Entry.objects.filter(entry_type=type).values()), safe=False)

@csrf_exempt
def api_entry(request, id):
    if request.method == 'DELETE':
        return JsonResponse({"deleted": id}) # TODO
    return JsonResponse(list(Entry.objects.filter(id=id).values())[0], safe=False)

@csrf_exempt
def api_new_entry(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        entry = Entry.new(data.get('username').lower(), data.get('uid').lower(), data.get('task_type'))
        return JsonResponse(list(Entry.objects.filter(id=entry.id).values())[0], safe=False)
