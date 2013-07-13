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
    stats = {}
    stats['issue_count'] = Issue.objects.count()
    stats['agenda_item_count'] = AgendaItem.objects.count()
    stats['meeting_count'] = Meeting.objects.count()
    stats['issue_geo_count'] = Issue.objects.filter(issuegeometry__isnull=False).distinct().count()
    args = get_js_paths()
    args['stats'] = stats
    return render_to_response('home.html', args)

def meeting_list(request):
    return render_to_response('meeting_list.html', get_js_paths())

def meeting_details(request, slug):
    meeting = get_object_or_404(Meeting, pk=slug)
    return render_to_response('meeting_details.html', get_js_paths())

def issue_list(request, slug):
    return render_to_response('issue_list.html', get_js_paths())

def issue_details(request, slug):
    issue = get_object_or_404(Issue, slug=slug)
    args = get_js_paths()
    args['issue'] = issue
    return render_to_response('issue_details.html', args)
