from mongoengine import *

class ZipDocument(Document):
    origin_id = StringField(required=True)
    organisation = StringField(required=True)
    committee = StringField(required=True)
    date = DateTimeField(required=True)
    meeting_nr = IntField(required=True)
    url = URLField(required=True)
    cleaned_xml_url = URLField()
