import json
from django.contrib.gis.geos import Polygon
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.exceptions import InvalidFilterError
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.contrib.gis.resources import ModelResource as GeoModelResource
from ahjodoc.models import *

class CommitteeResource(ModelResource):
    class Meta:
        queryset = Committee.objects.all()
        resource_name = 'committee'

class CategoryResource(ModelResource):
    class Meta:
        queryset = Category.objects.all()
        resource_name = 'category'

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

class MeetingDocumentResource(ModelResource):
    meeting = fields.ToOneField(MeetingResource, 'meeting', full=True)
    class Meta:
        queryset = MeetingDocument.objects.order_by('-last_modified_time')
        resource_name = 'meeting_document'
        filtering = {
            'type': ALL,
            'meeting': ALL_WITH_RELATIONS,
            'publish_time': ALL,
            'date': ALL
        }
        ordering = ('date', 'publish_time')

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

class ItemResource(ModelResource):
    category = fields.ToOneField(CategoryResource, 'category')

    def apply_filters(self, request, applicable_filters):
        ret = super(ItemResource, self).apply_filters(request, applicable_filters)
        if 'itemgeometry__in' in applicable_filters:
            ret = ret.distinct()
        return ret

    def build_filters(self, filters=None):
        orm_filters = super(ItemResource, self).build_filters(filters)
        if filters and 'bbox' in filters:
            bbox_filter = build_bbox_filter(filters['bbox'], 'geometry')
            geom_list = ItemGeometry.objects.filter(**bbox_filter)
            orm_filters['itemgeometry__in'] = geom_list
        return orm_filters

    def dehydrate(self, bundle):
        obj = bundle.obj
        bundle.data['category_origin_id'] = obj.category.origin_id
        bundle.data['category_name'] = obj.category.name
        geometries = []
        for geom in obj.itemgeometry_set.all():
            d = json.loads(geom.geometry.geojson)
            d['name'] = geom.name
            geometries.append(d)
        bundle.data['geometries'] = geometries
        return bundle
    class Meta:
        queryset = Item.objects.all().select_related('category')
        resource_name = 'item'
        filtering = {
            'register_id': ALL,
            'slug': ALL,
        }

class ItemGeometryResource(ModelResource):
    item = fields.ToOneField(ItemResource, 'item')

    class Meta:
        queryset = ItemGeometry.objects.all()
        resource_name = 'item_geometry'
        filtering = {
            'item': ALL_WITH_RELATIONS
        }
    
class AgendaItemResource(ModelResource):
    meeting = fields.ToOneField(MeetingResource, 'meeting', full=True)
    item = fields.ToOneField(ItemResource, 'item', full=True)

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
        queryset = AgendaItem.objects.all().select_related('item')
        resource_name = 'agenda_item'
        filtering = {
            'meeting': ALL_WITH_RELATIONS,
            'item': ALL_WITH_RELATIONS
        }
        ordering = ('last_modified_time', 'meeting')

all_resources = [
    MeetingDocumentResource, CommitteeResource, CategoryResource,
    MeetingResource, ItemResource, AgendaItemResource
]
