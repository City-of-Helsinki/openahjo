# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from ahjodoc.models import *
from ahjodoc.api import *
from munigeo.api import DistrictResource
from django.templatetags.static import static
from django.core.urlresolvers import get_script_prefix
from django.shortcuts import redirect

# Cache the JSON encodings for some rarely changing data here.
category_json = None
district_json = None

def get_js_paths():
    prefix = get_script_prefix()
    debug = "true" if settings.DEBUG else "false"
    return {
        'API_PREFIX': prefix,
        'GEOCODER_API_URL': settings.GEOCODER_API_URL,
        'DEBUG': debug
    }

def get_metadata(request, info):
    props = []
    props.append({'name': 'og:image', 'content': request.build_absolute_uri(static('img/share-image-154x154.png'))})
    if 'description' in info:
        props.append({'name': 'og:description', 'content': info['description']})
    if 'title' in info:
        props.append({'name': 'og:title', 'content': info['title']})
    props.append({'name': 'og:url', 'content': request.build_absolute_uri(request.path)})
    return {'meta_properties': props}

def render_view(request, template, args={}):
    args.update(get_js_paths())
    args.update(get_metadata(request, args))
    return render_to_response(template, args)

def get_policymakers(request):
    res = PolicymakerResource()
    pm_list = Policymaker.objects.filter(abbreviation__isnull=False)
    bundles = []
    for obj in pm_list:
        bundle = res.build_bundle(obj=obj, request=request)
        bundles.append(res.full_dehydrate(bundle, for_list=True))
    json = res.serialize(None, bundles, "application/json")
    return json

def get_categories(request):
    global category_json

    if category_json:
        return category_json
    res = CategoryResource()
    cat_list = Category.objects.filter(level__lte=1)
    bundles = []
    for obj in cat_list:
        bundle = res.build_bundle(obj=obj, request=request)
        bundles.append(res.full_dehydrate(bundle, for_list=True))
    json = res.serialize(None, bundles, "application/json")
    category_json = json
    return json

def get_districts(request):
    global district_json

    if district_json:
        return district_json
    res = DistrictResource()
    obj_list = District.objects.all()
    bundles = []
    for obj in obj_list:
        bundle = res.build_bundle(obj=obj, request=request)
        data = res.full_dehydrate(bundle, for_list=True)
        del bundle.data['borders']
        del bundle.data['municipality']
        bundles.append(data)
    json = res.serialize(None, bundles, "application/json")
    district_json = json
    return json


def home_view(request):
    args = {'pm_list_json': get_policymakers(request)}
    args['title'] = 'Helsingin kaupungin Päätökset-palvelu'
    args['description'] = 'Löydä juuri sinua kiinnostavat Helsingin kaupungin poliittiset päätökset.'
    return render_view(request, 'home.html', args)

def issue_view(request, template, args={}):
    args['cat_list_json'] = get_categories(request)
    args['pm_list_json'] = get_policymakers(request)
    args['district_list_json'] = get_districts(request)

    return render_view(request, template, args)

def issue_list(request):
    args = {'title': 'Asiat', 'description': 'Hae kaupungin päätöksiä.'}
    return issue_view(request, 'issue.html', args)
def issue_list_map(request):
    args = {'title': 'Asiat kartalla', 'description': 'Tarkastele kaupungin päätöksiä kartalla.'}
    return issue_view(request, 'issue.html')

def issue_details(request, slug, pm_slug=None, year=None, number=None, index=None):
    issue = get_object_or_404(Issue, slug=slug)

    args = {}
    args['issue'] = issue
    if pm_slug:
        filter_args = {
            'issue': issue,
            'meeting__policymaker__slug': pm_slug,
            'meeting__year': year,
            'meeting__number': number
        }
        if index is None:
            try:
                queryset = AgendaItem.objects.filter(**filter_args)
                agenda_item = AgendaItem.objects.filter(**filter_args).first()
                if len(queryset) > 1:
                    # If multiple agenda items for same issue in same meeting,
                    # redirect to first
                    return redirect(issue_details, pm_slug=pm_slug, slug=slug, year=year,
                        number=number, index=unicode(agenda_item.index))
            except AgendaItem.DoesNotExist:
                raise Http404("Agenda item not found")
        else:
            del filter_args['issue']
            filter_args['index'] = int(index)
            agenda_item = get_object_or_404(AgendaItem, **filter_args)

        args['title'] = agenda_item.subject
        summary = agenda_item.get_summary()
    else:
        args['title'] = issue.subject
        summary = issue.determine_summary()

    if summary:
        # Get first sentences
        s = summary.split('.')
        desc = '.'.join(s[0:3])
        args['description'] = desc + '.'

    res = IssueResource()
    bundle = res.build_bundle(obj=issue, request=request)
    data = res.full_dehydrate(bundle, for_list=False)
    json = res.serialize(None, data, "application/json")
    args['issue_json'] = json

    res = AgendaItemResource()
    pm_list = AgendaItem.objects.filter(issue=issue)
    bundles = []
    for obj in pm_list:
        bundle = res.build_bundle(obj=obj, request=request)
        bundles.append(res.full_dehydrate(bundle, for_list=False))
    json = res.serialize(None, bundles, "application/json")
    args['ai_list_json'] = json

    return issue_view(request, 'issue.html', args)

def policymaker_view(request, template, args={}):
    args['pm_list_json'] = get_policymakers(request)
    return render_view(request, template, args)

def policymaker_list(request):
    return policymaker_view(request, 'policymaker.html')

def policymaker_details(request, slug, year=None, number=None, index=None):
    org = get_object_or_404(Organization, slug=slug)
    args = {}

    res = OrganizationResource()
    old_get = request.GET # argh
    request.GET = dict(children='true') # argh2 
    bundle = res.build_bundle(obj=org, request=request)
    org_dict = res.full_dehydrate(bundle, for_list=False)
    args['organization_json'] = res.serialize(None, org_dict, 'application/json')
    request.GET = old_get

    args['organization'] = org
    args['policymaker'] = org.policymaker
    if year:
        args['meeting_year'] = year
        args['meeting_number'] = number
    return policymaker_view(request, 'policymaker.html', args)

def about(request):
    return render_view(request, "about.html")
