from django.db import models

class MeetingDocument(models.Model):
    origin_id = models.CharField(max_length=50)
    organisation = models.CharField(max_length=20)
    committee = models.CharField(max_length=20)
    date = models.DateField()
    meeting_nr = models.PositiveIntegerField()
    origin_url = models.URLField()
    xml_url = models.URLField(null=True, blank=True)
