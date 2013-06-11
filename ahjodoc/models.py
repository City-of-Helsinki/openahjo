from django.conf import settings
from django.contrib.gis.db import models
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey

class Committee(models.Model):
    name = models.CharField(max_length=100, help_text='Name of committee')
    abbreviation = models.CharField(max_length=20, null=True, help_text='Official abbreviation')
    origin_id = models.CharField(max_length=20, db_index=True, help_text='ID string in upstream system')

    def __unicode__(self):
        return self.name

class Meeting(models.Model):
    committee = models.ForeignKey(Committee, help_text='Committee or other organization')
    date = models.DateField(db_index=True, help_text='Date of the meeting')
    number = models.PositiveIntegerField(help_text='Meeting number for the committee')
    year = models.PositiveIntegerField(help_text='Year the meeting is held')
    issues = models.ManyToManyField('Issue', through='AgendaItem')
    minutes = models.BooleanField(help_text='Meeting minutes document available')

    def __unicode__(self):
        return u"%s %d/%d (%s)" % (self.committee, self.number, self.year, self.date) 

    class Meta:
        unique_together = (('committee', 'date'), ('committee', 'year', 'number'))

class MeetingDocument(models.Model):
    meeting = models.ForeignKey(Meeting)
    origin_id = models.CharField(max_length=50, unique=True, help_text='ID string in upstream system')
    # Either 'agenda' or 'minutes'
    type = models.CharField(max_length=20, help_text='Meeting document type (either \'agenda\' or \'minutes\')')
    organisation = models.CharField(max_length=20)

    last_modified_time = models.DateTimeField(help_text='Time when the meeting information last changed')
    publish_time = models.DateTimeField(help_text='Time when the meeting document was scheduled for publishing')
    origin_url = models.URLField(help_text='Link to the upstream file')
    xml_file = models.FileField(upload_to=settings.AHJO_PATHS['xml'])

class Category(MPTTModel):
    origin_id = models.CharField(max_length=20, unique=True, help_text='ID string in upstream system')
    name = models.CharField(max_length=100, db_index=True, help_text='Full category name')
    parent = TreeForeignKey('self', null=True, blank=True, help_text='Parent category')

    class Meta:
        verbose_name_plural = 'categories'

    class MPTTMeta:
        order_insertion_by = ['origin_id']

class Issue(models.Model):
    register_id = models.CharField(max_length=20, db_index=True, unique=True,
                                   help_text='Issue archival ID')
    slug = models.CharField(max_length=50, db_index=True, unique=True,
                            help_text='Unique slug (generated from register_id)')
    subject = models.CharField(max_length=500, help_text='One-line description for issue')
    category = models.ForeignKey(Category, db_index=True, help_text='Issue category')

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
    PASSED = "PASSED_UNCHANGED"
    PASSED_VOTED = "PASSED_VOTED"
    PASSED_REVISED = "PASSED_REVISED"
    PASSED_MODIFIED = "PASSED_MODIFIED"
    REJECTED = "REJECTED"
    NOTED = "NOTED"
    RETURNED = "RETURNED"
    REMOVED = "REMOVED"
    TABLED = "TABLED"
    ELECTION = "ELECTION"
    RESOLUTION_CHOICES = (
        (PASSED, 'Passed as drafted'),
        (PASSED_VOTED, 'Passed after a vote'),
        (PASSED_REVISED, 'Passed revised by presenter'),
        (PASSED_MODIFIED, 'Passed modified'),
        (REJECTED, 'Rejected'),
        (NOTED, 'Noted as informational'),
        (RETURNED, 'Returned to preparation'),
        (REMOVED, 'Removed from agenda'),
        (TABLED, 'Tabled'),
        (ELECTION, 'Election'),
    )
    meeting = models.ForeignKey(Meeting, db_index=True, help_text='Meeting for the agenda item')
    issue = models.ForeignKey(Issue, db_index=True, help_text='Issue for the item')
    index = models.PositiveIntegerField(help_text='Item number on the agenda')
    subject = models.CharField(max_length=500, help_text='One-line description for agenda item')
    from_minutes = models.BooleanField(help_text='Do the contents come from the minutes document?')
    last_modified_time = models.DateTimeField(db_index=True, help_text='Time of last modification')
    resolution = models.CharField(max_length=20, choices=RESOLUTION_CHOICES, null=True, help_text="Type of resolution made")

    def __unicode__(self):
        if self.issue:
            return u"%s / #%d: %s (%s)" % (self.meeting, self.index, self.subject,
                                           self.issue.register_id)
        else:
            return u"%s / #%d: %s" % (self.meeting, self.index, self.subject)

    class Meta:
        unique_together = (('meeting', 'issue'), ('meeting', 'index'))
        ordering = ('meeting', 'index')

class Attachment(models.Model):
    agenda_item = models.ForeignKey(AgendaItem, db_index=True)
    number = models.PositiveIntegerField(help_text='Index number of the item attachment')
    name = models.CharField(max_length=250, null=True, help_text='Short name for the agenda item')
    public = models.BooleanField(help_text='Is attachment public?')
    file = models.FileField(upload_to=settings.AHJO_PATHS['attachment'], null=True)
    hash = models.CharField(max_length=50, null=True, help_text='SHA-1 hash of the file contents')
    file_type = models.CharField(max_length=10, null=True, help_text='File extension')

    class Meta:
        unique_together = (('agenda_item', 'number'),)
        ordering = ('agenda_item', 'number')

class ContentSection(models.Model):
    # Either draft resolution, summary, presenter, resolution or hearing
    type = models.CharField(max_length=50)
    # Content sections are bound to meetings
    agenda_item = models.ForeignKey(AgendaItem, db_index=True)
    index = models.PositiveIntegerField()
    # Content in HTML, paragraphs separated by '\n'
    text = models.TextField()

    class Meta:
        unique_together = (('agenda_item', 'index'),)
        ordering = ('agenda_item', 'index')

class Video(models.Model):
    meeting = models.ForeignKey(Meeting, db_index=True)
    # If agenda_item is null, video is for the whole meeting.
    agenda_item = models.ForeignKey(AgendaItem, null=True, db_index=True)
    url = models.URLField()
    index = models.PositiveIntegerField(help_text='Video number within the agenda item')
    start_pos = models.FloatField()
    duration = models.FloatField()
    speaker = models.CharField(max_length=50, null=True, db_index=True)
    party = models.CharField(max_length=50, null=True)
    screenshot = models.FileField(upload_to=settings.AHJO_PATHS['video'])

    class Meta:
        unique_together = (('meeting', 'agenda_item', 'start_pos'),)
        ordering = ('agenda_item', 'start_pos')
