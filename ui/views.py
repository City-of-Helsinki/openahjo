from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from ahjodoc.models import *

def home_view(request):
    prefix = getattr(settings, 'URL_PREFIX', '')
    return render_to_response('home.html', {'API_PREFIX': '/' + prefix})

def item_view(request, slug):
    item = get_object_or_404(Item, slug=slug)
    prefix = getattr(settings, 'URL_PREFIX', '')
    return render_to_response('item.html', {'API_PREFIX': '/' + prefix, 'item': item})
