from django.conf import settings
from django.contrib.gis.db import models
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey

class Committee(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20, null=True)
    origin_id = models.CharField(max_length=20, db_index=True)

class Meeting(models.Model):
    committee = models.ForeignKey(Committee)
    date = models.DateField(db_index=True)
    number = models.PositiveIntegerField(help_text='Meeting number for the committee')
    year = models.PositiveIntegerField()
    issues = models.ManyToManyField('Issue', through='AgendaItem')
    minutes = models.BooleanField(help_text='Minutes document available')

    class Meta:
        unique_together = (('committee', 'date'), ('committee', 'year', 'number'))

class MeetingDocument(models.Model):
    meeting = models.ForeignKey(Meeting)
    origin_id = models.CharField(max_length=50, unique=True)
    # Either 'agenda' or 'minutes'
    type = models.CharField(max_length=20)
    organisation = models.CharField(max_length=20)

    last_modified_time = models.DateTimeField()
    publish_time = models.DateTimeField()
    origin_url = models.URLField()
    xml_file = models.FileField(upload_to=settings.AHJO_XML_PATH)

class Category(MPTTModel):
    origin_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, db_index=True)
    parent = TreeForeignKey('self', null=True, blank=True)

    class MPTTMeta:
        order_insertion_by = ['origin_id']

class Issue(models.Model):
    register_id = models.CharField(max_length=20, db_index=True, unique=True)
    slug = models.CharField(max_length=50, db_index=True, unique=True)
    subject = models.CharField(max_length=500)
    category = models.ForeignKey(Category, db_index=True)

    def save(self, *args, **kwargs):
        if not self.pk and not self.slug:
            self.slug = slugify(unicode(self.register_id))
        return super(Issue, self).save(*args, **kwargs)
    def __unicode__(self):
        return "%s: %s" % (self.register_id, self.subject)

class IssueGeometry(models.Model):
    issue = models.ForeignKey(Issue)
    name = models.CharField(max_length=100)
    geometry = models.GeometryField()    

    objects = models.GeoManager()

class AgendaItem(models.Model):
    meeting = models.ForeignKey(Meeting, db_index=True)
    issue = models.ForeignKey(Issue, db_index=True)
    index = models.PositiveIntegerField()
    from_minutes = models.BooleanField()
    last_modified_time = models.DateTimeField(db_index=True)

    class Meta:
        unique_together = (('meeting', 'issue'), ('meeting', 'index'))

class Attachment(models.Model):
    agenda_item = models.ForeignKey(AgendaItem, db_index=True)
    number = models.PositiveIntegerField()
    name = models.CharField(max_length=250, null=True)
    public = models.BooleanField()
    file = models.FileField(upload_to=settings.AHJO_ATTACHMENT_PATH, null=True)
    hash = models.CharField(max_length=50, null=True)
    file_type = models.CharField(max_length=10, null=True)

    class Meta:
        unique_together = (('agenda_item', 'number'),)
        ordering = ('agenda_item', 'number')

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
