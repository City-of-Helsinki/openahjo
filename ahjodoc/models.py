from django.conf import settings
from django.db import models

class MeetingDocument(models.Model):
    origin_id = models.CharField(max_length=50)
    # Either 'agenda' or 'minutes'
    type = models.CharField(max_length=20)
    organisation = models.CharField(max_length=20)
    committee = models.CharField(max_length=20)
    publish_time = models.DateTimeField()
    date = models.DateField()
    meeting_nr = models.PositiveIntegerField()
    origin_url = models.URLField()
    xml_file = models.FileField(upload_to=settings.AHJO_XML_PATH)
