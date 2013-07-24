from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from ahjodoc.models import *
from ahjodoc.api import *

def get_js_paths():
    prefix = getattr(settings, 'URL_PREFIX', '')
    debug = "true" if settings.DEBUG else "false"
    return {
        'API_PREFIX': '/' + prefix,
        'GEOCODER_API_URL': settings.GEOCODER_API_URL,
        'DEBUG': debug
    }

def render_view(request, template, args={}):
    args.update(get_js_paths())
    return render_to_response(template, args)

def home_view(request):
    """
    stats = {}
    stats['issue_count'] = Issue.objects.count()
    stats['agenda_item_count'] = AgendaItem.objects.count()
    stats['meeting_count'] = Meeting.objects.count()
    stats['issue_geo_count'] = Issue.objects.filter(issuegeometry__isnull=False).distinct().count()
    args['stats'] = stats
    """
    return render_view(request, 'home.html')

def meeting_list(request):
    return render_view(request, 'meeting_list.html')

def meeting_details(request, slug):
    meeting = get_object_or_404(Meeting, pk=slug)
    return render_view(request, 'meeting_details.html')

def issue_list(request):
    return render_view(request, 'issue_list.html')

def issue_details(request, slug):
    issue = get_object_or_404(Issue, slug=slug)
    args = {}
    args['issue'] = issue
    return render_view(request, 'issue_details.html', args)

def policymaker_view(request, template, args={}):
    res = PolicymakerResource()
    req_bundle = res.build_bundle(request=request)
    pm_list = Policymaker.objects.filter(abbreviation__isnull=False)
    bundles = []
    for obj in pm_list:
        bundle = res.build_bundle(obj=obj, request=request)
        bundles.append(res.full_dehydrate(bundle, for_list=True))
    json = res.serialize(None, bundles, "application/json")

    args['pm_list_json'] = json
    
    return render_view(request, template, args)

def policymaker_list(request):
    return policymaker_view(request, 'policymaker_list.html')

def policymaker_details(request, slug):
    pm = get_object_or_404(Policymaker, slug=slug)
    args = {}
    args['policymaker'] = pm
    return policymaker_view(request, 'policymaker_details.html', args)
