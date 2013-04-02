from tastypie.resources import ModelResource
from ahjodoc.models import *

class MeetingDocument(ModelResource):
    class Meta:
        queryset = MeetingDocument.objects.all()
        resource_name = 'meeting_document'

all_resources = [MeetingDocument]
