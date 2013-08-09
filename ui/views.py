from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from ahjodoc.models import *
from ahjodoc.api import *

# Cache the JSON encodings for some rarely changing data here.
policymaker_json = None
category_json = None

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

def get_policymakers(request):
    global policymaker_json

    if policymaker_json:
        return policymaker_json
    res = PolicymakerResource()
    req_bundle = res.build_bundle(request=request)
    pm_list = Policymaker.objects.filter(abbreviation__isnull=False)
    bundles = []
    for obj in pm_list:
        bundle = res.build_bundle(obj=obj, request=request)
        bundles.append(res.full_dehydrate(bundle, for_list=True))
    json = res.serialize(None, bundles, "application/json")
    policymaker_json = json
    return json

def get_categories(request):
    global category_json

    if category_json:
        return category_json
    res = CategoryResource()
    req_bundle = res.build_bundle(request=request)
    cat_list = Category.objects.filter(level__lte=1)
    bundles = []
    for obj in cat_list:
        bundle = res.build_bundle(obj=obj, request=request)
        bundles.append(res.full_dehydrate(bundle, for_list=True))
    json = res.serialize(None, bundles, "application/json")
    category_json = json
    return json

def home_view(request):
    args = {'pm_list_json': get_policymakers(request)}
    return render_view(request, 'home.html', args)

def issue_view(request, template, args={}):
    args['cat_list_json'] = get_categories(request)
    args['pm_list_json'] = get_policymakers(request)

    return render_view(request, template, args)

def issue_list(request):
    return issue_view(request, 'issue_list.html')
def issue_list_map(request):
    return issue_view(request, 'issue_list.html')

def issue_details(request, slug):
    issue = get_object_or_404(Issue, slug=slug)
    args = {}
    args['issue'] = issue
    return issue_view(request, 'issue_details.html', args)

def policymaker_view(request, template, args={}):
    args['pm_list_json'] = get_policymakers(request)

    return render_view(request, template, args)

def policymaker_list(request):
    return policymaker_view(request, 'policymaker_list.html')

def policymaker_details(request, slug, year=None, number=None):
    pm = get_object_or_404(Policymaker, slug=slug)
    args = {}
    args['policymaker'] = pm
    if year:
        args['meeting_year'] = year
        args['meeting_number'] = number
    return policymaker_view(request, 'policymaker_list.html', args)
