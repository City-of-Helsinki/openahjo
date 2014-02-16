import re

from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.gis.db import models
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey
from munigeo.models import District
from django.utils.html import strip_tags


def truncate_chars(value, max_length):
    if len(value) > max_length:
        truncd_val = value[:max_length]
        if not len(value) == max_length+1 and value[max_length+1] != " ":
            truncd_val = truncd_val[:truncd_val.rfind(" ")]
        return  truncd_val + "..."
    return value


class Policymaker(models.Model):
    name = models.CharField(max_length=100, help_text='Name of policymaker')
    abbreviation = models.CharField(max_length=20, null=True, help_text='Official abbreviation')
    slug = models.CharField(max_length=50, db_index=True, unique=True, null=True, help_text='Unique slug')
    origin_id = models.CharField(max_length=20, db_index=True, help_text='ID string in upstream system')
    summary = models.TextField(null=True)

    def save(self, *args, **kwargs):
        if not self.slug and self.abbreviation:
            self.slug = slugify(unicode(self.abbreviation))
        return super(Policymaker, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

class Meeting(models.Model):
    policymaker = models.ForeignKey(Policymaker, help_text='Policymaker or other organization')
    date = models.DateField(db_index=True, help_text='Date of the meeting')
    number = models.PositiveIntegerField(help_text='Meeting number for the policymaker')
    year = models.PositiveIntegerField(help_text='Year the meeting is held')
    issues = models.ManyToManyField('Issue', through='AgendaItem')
    minutes = models.BooleanField(help_text='Meeting minutes document available')

    def __unicode__(self):
        return u"%s %d/%d (%s)" % (self.policymaker, self.number, self.year, self.date) 

    class Meta:
        unique_together = (('policymaker', 'date'), ('policymaker', 'year', 'number'))

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

    def __unicode__(self):
        return u"%s %s" % (self.origin_id, self.name)

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
    latest_decision_date = models.DateField(null=True, help_text='Date of the latest meeting where the issue was/will be discussed')
    last_modified_time = models.DateTimeField(auto_now=True, null=True)
    origin_id = models.CharField(max_length=50, null=True,
                                 help_text='ID field in the upstream source')

    geometries = models.ManyToManyField('IssueGeometry')
    districts = models.ManyToManyField(District)
    keywords = models.ManyToManyField('IssueKeyword')

    def find_most_descriptive_agenda_item(self):
        ai_list = AgendaItem.objects.filter(issue=self).order_by('meeting__date')

        # First try city board
        for ai in ai_list:
            if ai.meeting.policymaker.origin_id == '00400':
                return ai

        # Then city council
        for ai in ai_list:
            if ai.meeting.policymaker.origin_id == '02900':
                return ai

        # Then just the first one that doesn't include 'lausunto'
        for ai in ai_list:
            if not 'lausunto' in ai.subject.lower():
                return ai

        # Finally just the latest agenda item
        if len(ai_list):
            return ai_list[0]
        else:
            return None

    def determine_subject(self):
        ai = self.find_most_descriptive_agenda_item()
        if ai:
            return ai.subject
        else:
            return self.subject

    def determine_latest_decision_date(self):
        ai_list = AgendaItem.objects.filter(issue=self).order_by('-meeting__date')
        return ai_list[0].meeting.date

    def determine_summary(self):
        ai = self.find_most_descriptive_agenda_item()
        if not ai:
            return None
        return ai.get_summary()

    def save(self, *args, **kwargs):
        if not self.pk and not self.slug:
            self.slug = slugify(unicode(self.register_id))
        return super(Issue, self).save(*args, **kwargs)
    def __unicode__(self):
        return "%s: %s" % (self.register_id, self.subject)

class IssueGeometry(models.Model):
    TYPES = (
        ('address', 'Address'),
        ('plan', 'Plan'),
        ('district', 'District'),
    )
    name = models.CharField(max_length=100, db_index=True)
    type = models.CharField(max_length=20, choices=TYPES, db_index=True)
    geometry = models.GeometryField()

    objects = models.GeoManager()

    class Meta:
        unique_together = (('name', 'type'),)

class IssueKeyword(models.Model):
    name = models.CharField(max_length=150 , db_index=True, unique=True)

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
    last_modified_time = models.DateTimeField(db_index=True, auto_now=True, help_text='Time of last modification')
    origin_last_modified_time = models.DateTimeField(db_index=True, null=True, help_text='Time of last modification in data source')
    resolution = models.CharField(max_length=20, choices=RESOLUTION_CHOICES, null=True, help_text="Type of resolution made")
    preparer = models.CharField(max_length=100, null=True, help_text="Name of the person who prepared the issue")
    introducer = models.CharField(max_length=100, null=True, help_text="Name of the person who introduced the issue in the meeting")

    def get_summary(self):
        c_list = list(ContentSection.objects.filter(agenda_item=self).order_by('index'))
        content = None
        for c_type in ("summary", "presenter"):
            for content in c_list:
                if content.type == c_type:
                    break
            else:
                continue
            break
        else:
            return None

        text = content.text
        # Use only the first paragraph
        idx = text.find('<p')
        if idx >= 0:
            text = text[idx:]
        idx = text.find('</p>')
        if idx >= 0:
            text = text[0:idx+4]

        text = truncate_chars(strip_tags(text), 1000)
        return text

    def get_absolute_url(self):
        return reverse('ui.views.issue_details', kwargs={'slug': self.issue.slug})

    def save(self, *args, **kwargs):
        ret = super(AgendaItem, self).save(*args, **kwargs)
        issue = self.issue
        subject = issue.determine_subject()
        if subject != issue.subject:
            issue.subject = subject
            issue.save()
        return ret

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
    name = models.CharField(max_length=400, null=True, help_text='Short name for the agenda item')
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
