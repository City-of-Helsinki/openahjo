from tastypie.resources import ModelResource
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from ahjodoc.models import *

class MeetingDocument(ModelResource):
    class Meta:
        queryset = MeetingDocument.objects.order_by('-publish_time')
        resource_name = 'meeting_document'
        filtering = {
            'type': ALL,
            'committee': ALL,
            'publish_time': ALL,
            'meeting_nr': ALL,
            'date': ALL
        }

all_resources = [MeetingDocument]
