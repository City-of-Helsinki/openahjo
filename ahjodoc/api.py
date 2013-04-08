from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from ahjodoc.models import *

class MeetingDocumentResource(ModelResource):
    class Meta:
        queryset = MeetingDocument.objects.order_by('-last_modified_time')
        resource_name = 'meeting_document'
        filtering = {
            'type': ALL,
            'committee': ALL,
            'publish_time': ALL,
            'meeting_nr': ALL,
            'date': ALL
        }

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

class ItemResource(ModelResource):
    class Meta:
        queryset = Item.objects.all()
        resource_name = 'item'
        filtering = {
            'register_id': ALL
        }
    
class AgendaItemResource(ModelResource):
    meeting = fields.ToOneField(MeetingResource, 'meeting')
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

all_resources = [
    MeetingDocumentResource, CommitteeResource, CategoryResource,
    MeetingResource, ItemResource, AgendaItemResource
]
