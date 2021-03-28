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
    entry.cleanup()

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
    entry = get_object_or_404(Entry, pk=id)
    if request.method == 'DELETE':
        entry.cleanup()
        return JsonResponse({"deleted": id})
    #return JsonResponse(list(Entry.objects.filter(id=entry.id).values())[0], safe=False)
    dump = entry.dump()
    if 'proxmox' in entry.vm["state"]:
        dump.update({"status": entry.vm["state"]["proxmox"]["status"]})
    else:
        dump.update({"status": "new"})
    return JsonResponse(dump)

@csrf_exempt
def api_new_entry(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        entry = Entry.new(data.get('username').lower(), data.get('uid').lower(), data.get('track_id', "1"))
        #return JsonResponse(list(Entry.objects.filter(id=entry.id).values())[0], safe=False)
        dump = entry.dump()
        dump.update({"status": "new"})
        return JsonResponse(dump)
