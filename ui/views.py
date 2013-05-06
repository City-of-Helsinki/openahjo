from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from ahjodoc.models import *

def get_js_paths():
    prefix = getattr(settings, 'URL_PREFIX', '')
    debug = "true" if settings.DEBUG else "false"
    return {
        'API_PREFIX': '/' + prefix,
        'GEOCODER_API_URL': settings.GEOCODER_API_URL,
        'DEBUG': debug
    }

def home_view(request):
    return render_to_response('home.html', get_js_paths())

def issue_view(request, slug):
    issue = get_object_or_404(Issue, slug=slug)
    prefix = getattr(settings, 'URL_PREFIX', '')
    args = get_js_paths()
    args['issue'] = issue
    return render_to_response('issue.html', args)
