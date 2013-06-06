import json
import urlparse
from django.contrib.gis.geos import Polygon
from django.utils.html import strip_tags
from django.conf import settings
from django.db.models import Count, Sum
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.exceptions import InvalidFilterError
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.cache import SimpleCache
from tastypie.contrib.gis.resources import ModelResource as GeoModelResource
from ahjodoc.models import *

CACHE_TIMEOUT = 600

class CommitteeResource(ModelResource):
    def apply_filters(self, request, filters):
        qs = super(CommitteeResource, self).apply_filters(request, filters)
        meetings = request.GET.get('meetings', '')
        if meetings.lower() not in ('0', 'false'):
            # Include only categories with associated issues
            qs = qs.annotate(num_meetings=Count('meeting')).filter(num_meetings__gt=0)
        return qs
    class Meta:
        queryset = Committee.objects.all()
        resource_name = 'committee'
        ordering = ('name',)
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        cache = SimpleCache(timeout=CACHE_TIMEOUT)

class CategoryResource(ModelResource):
    parent = fields.ToOneField('self', 'parent', null=True)

    def query_to_filters(self, query):
        filters = {}
        filters['name__icontains'] = query
        return filters

    def build_filters(self, filters=None):
        orm_filters = super(CategoryResource, self).build_filters(filters)
        if filters and 'input' in filters:
            orm_filters.update(self.query_to_filters(filters['input']))
        return orm_filters            

    def apply_filters(self, request, filters):
        qs = super(CategoryResource, self).apply_filters(request, filters)
        issues = request.GET.get('issues', '')
        if issues.lower() not in ('0', 'false'):
            # Include only categories with associated issues
            qs = qs.annotate(num_issues=Count('issue')).filter(num_issues__gt=0)
        return qs
    def dehydrate(self, bundle):
        if getattr(bundle.obj, 'num_issues'):
            bundle.data['num_issues'] = bundle.obj.num_issues
        return bundle

    class Meta:
        queryset = Category.objects.all()
        excludes = ['lft', 'rght', 'tree_id']
        resource_name = 'category'
        filtering = {
            'level': ALL,
            'name': ALL,
            'origin_id': ALL,
        }
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        cache = SimpleCache(timeout=CACHE_TIMEOUT)

class MeetingResource(ModelResource):
    committee = fields.ToOneField(CommitteeResource, 'committee')

    def dehydrate(self, bundle):
        obj = bundle.obj
        bundle.data['committee_name'] = obj.committee.name
        return bundle

    class Meta:
        queryset = Meeting.objects.order_by('-date').select_related('committee')
        resource_name = 'meeting'
        filtering = {
            'committee': ALL_WITH_RELATIONS
        }
        ordering = ('date', 'committee')
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        cache = SimpleCache(timeout=CACHE_TIMEOUT)

class MeetingDocumentResource(ModelResource):
    meeting = fields.ToOneField(MeetingResource, 'meeting', full=True)
    xml_uri = fields.CharField()

    def dehydrate_xml_uri(self, bundle):
        uri = bundle.obj.xml_file.url
        if bundle.request:
            uri = bundle.request.build_absolute_uri(uri)
        return uri

    class Meta:
        queryset = MeetingDocument.objects.order_by('-last_modified_time')
        resource_name = 'meeting_document'
        excludes = ['xml_file']
        filtering = {
            'type': ALL,
            'meeting': ALL_WITH_RELATIONS,
            'publish_time': ALL,
            'date': ALL
        }
        ordering = ('date', 'publish_time')
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        cache = SimpleCache(timeout=CACHE_TIMEOUT)
    
def build_bbox_filter(bbox_val, field_name):
    points = bbox_val.split(',')
    if len(points) != 4:
        raise InvalidFilterError("bbox must be in format 'left,bottom,right,top'")
    try:
        points = [float(p) for p in points]
    except ValueError:
        raise InvalidFilterError("bbox values must be floating point")
    poly = Polygon.from_bbox(points)
    return {"%s__within" % field_name: poly}

class IssueResource(ModelResource):
    category = fields.ToOneField(CategoryResource, 'category')

    def apply_filters(self, request, applicable_filters):
        ret = super(IssueResource, self).apply_filters(request, applicable_filters)
        if 'issuegeometry__in' in applicable_filters:
            ret = ret.distinct()
        return ret

    def build_filters(self, filters=None):
        orm_filters = super(IssueResource, self).build_filters(filters)
        if filters and 'bbox' in filters:
            bbox_filter = build_bbox_filter(filters['bbox'], 'geometry')
            geom_list = IssueGeometry.objects.filter(**bbox_filter)
            orm_filters['issuegeometry__in'] = geom_list
        return orm_filters

    def dehydrate(self, bundle):
        obj = bundle.obj
        bundle.data['category_origin_id'] = obj.category.origin_id
        bundle.data['category_name'] = obj.category.name
        content_filter = ContentSection.objects.filter(agenda_item__issue=obj).order_by('-agenda_item__meeting__date')
        content = content_filter.filter(type="summary")
        if not content:
            content = content_filter.filter(type="presenter")
        if content:
            text = content[0].text
            idx = text.find('</p>')
            if idx >= 0:
                text = text[0:idx+4]
            if len(text) > 1000:
                text = text[0:1000]
            bundle.data['summary'] = strip_tags(text)
        geometries = []
        for geom in obj.issuegeometry_set.all():
            d = json.loads(geom.geometry.geojson)
            d['name'] = geom.name
            geometries.append(d)
        bundle.data['geometries'] = geometries
        return bundle
    class Meta:
        queryset = Issue.objects.all().select_related('category')
        resource_name = 'issue'
        filtering = {
            'register_id': ALL,
            'slug': ALL,
            'category': ALL_WITH_RELATIONS,
        }
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        cache = SimpleCache(timeout=CACHE_TIMEOUT)

class IssueGeometryResource(ModelResource):
    issue = fields.ToOneField(IssueResource, 'issue')

    class Meta:
        queryset = IssueGeometry.objects.all()
        resource_name = 'issue_geometry'
        filtering = {
            'issue': ALL_WITH_RELATIONS
        }
        cache = SimpleCache(timeout=CACHE_TIMEOUT)

class AgendaItemResource(ModelResource):
    meeting = fields.ToOneField(MeetingResource, 'meeting', full=True)
    issue = fields.ToOneField(IssueResource, 'issue', full=True)
    attachments = fields.ToManyField('ahjodoc.api.AttachmentResource', 'attachment_set', full=True, null=True)

    def dehydrate(self, bundle):
        obj = bundle.obj
        cs_list = ContentSection.objects.filter(agenda_item=obj)
        content = []
        for cs in cs_list:
            d = {'type': cs.type, 'text': cs.text}
            content.append(d)
        bundle.data['content'] = content            
        return bundle

    class Meta:
        queryset = AgendaItem.objects.all().select_related('issue')
        resource_name = 'agenda_item'
        filtering = {
            'meeting': ['exact', 'in'],
            'issue': ['exact', 'in'],
            'issue__category': ['exact', 'in'],
            'last_modified_time': ['gt', 'gte', 'lt', 'lte'],
        }
        ordering = ('last_modified_time', 'meeting', 'index')
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        cache = SimpleCache(timeout=CACHE_TIMEOUT)

class AttachmentResource(ModelResource):
    agenda_item = fields.ToOneField(AgendaItemResource, 'agenda_item')
    file_uri = fields.CharField(null=True)

    def dehydrate_file_uri(self, bundle):
        if not bundle.obj.file:
            return None
        uri = bundle.obj.file.url
        if bundle.request:
            uri = bundle.request.build_absolute_uri(uri)
        return uri

    class Meta:
        queryset = Attachment.objects.all()
        resource_name = 'attachment'
        excludes = ['file']
        filtering = {
            'agenda_item': ALL_WITH_RELATIONS,
            'hash': ALL,
            'number': ALL,
        }
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        cache = SimpleCache(timeout=CACHE_TIMEOUT)

class VideoResource(ModelResource):
    meeting = fields.ToOneField(MeetingResource, 'meeting')
    agenda_item = fields.ToOneField(AgendaItemResource, 'agenda_item', null=True)
    screenshot_uri = fields.CharField()

    def dehydrate_screenshot_uri(self, bundle):
        uri = bundle.obj.screenshot.url
        if bundle.request:
            uri = bundle.request.build_absolute_uri(uri)
        return uri

    class Meta:
        queryset = Video.objects.all()
        excludes = ['screenshot']
        filtering = {
            'meeting': ALL_WITH_RELATIONS,
            'agenda_item': ALL_WITH_RELATIONS,
            'index': ALL,
        }
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        cache = SimpleCache(timeout=CACHE_TIMEOUT)

all_resources = [
    MeetingDocumentResource, CommitteeResource, CategoryResource,
    MeetingResource, IssueResource, AgendaItemResource, AttachmentResource,
    VideoResource
]
