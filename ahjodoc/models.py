from django.conf import settings
from django.db import models

class Committee(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20, null=True)
    origin_id = models.CharField(max_length=20, db_index=True)

class Meeting(models.Model):
    committee = models.ForeignKey(Committee)
    date = models.DateField(db_index=True)
    number = models.PositiveIntegerField(help_text='Meeting number for the committee')
    year = models.PositiveIntegerField()
    items = models.ManyToManyField('Item', through='AgendaItem')
    minutes = models.BooleanField(help_text='Minutes document available')

    class Meta:
        unique_together = (('committee', 'date'), ('committee', 'year', 'number'))

class MeetingDocument(models.Model):
    origin_id = models.CharField(max_length=50)
    # Either 'agenda' or 'minutes'
    type = models.CharField(max_length=20)
    organisation = models.CharField(max_length=20)
    # FIXME: refer to Meeting instead
    committee = models.CharField(max_length=20)
    date = models.DateField()
    meeting_nr = models.PositiveIntegerField()
    last_modified_time = models.DateTimeField()
    publish_time = models.DateTimeField()
    origin_url = models.URLField()
    xml_file = models.FileField(upload_to=settings.AHJO_XML_PATH)

class Category(models.Model):
    origin_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True)

class Item(models.Model):
    register_id = models.CharField(max_length=20, db_index=True, unique=True)
    subject = models.CharField(max_length=500)
    category = models.ForeignKey(Category, db_index=True)

class AgendaItem(models.Model):
    meeting = models.ForeignKey(Meeting, db_index=True)
    item = models.ForeignKey(Item, db_index=True)
    index = models.PositiveIntegerField()

    class Meta:
        unique_together = (('meeting', 'item'), ('meeting', 'index'))

class ContentSection(models.Model):
    # Either draft resolution, summary, presenter, resolution or hearing
    type = models.CharField(max_length=20)
    # Content sections are bound to meetings
    agenda_item = models.ForeignKey(AgendaItem, db_index=True)
    index = models.PositiveIntegerField()
    # Content in HTML, paragraphs separated by '\n'
    text = models.TextField()

    class Meta:
        unique_together = (('agenda_item', 'index'),)
        ordering = ('agenda_item', 'index')
