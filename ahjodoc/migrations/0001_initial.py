# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mptt.fields
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('munigeo', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgendaItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('index', models.PositiveIntegerField(help_text=b'Item number on the agenda')),
                ('subject', models.CharField(help_text=b'One-line description for agenda item', max_length=500)),
                ('from_minutes', models.BooleanField(default=False, help_text=b'Do the contents come from the minutes document?')),
                ('last_modified_time', models.DateTimeField(help_text=b'Time of last modification', auto_now=True, db_index=True)),
                ('origin_last_modified_time', models.DateTimeField(help_text=b'Time of last modification in data source', null=True, db_index=True)),
                ('resolution', models.CharField(help_text=b'Type of resolution made', max_length=20, null=True, choices=[(b'PASSED_UNCHANGED', b'Passed as drafted'), (b'PASSED_VOTED', b'Passed after a vote'), (b'PASSED_REVISED', b'Passed revised by presenter'), (b'PASSED_MODIFIED', b'Passed modified'), (b'REJECTED', b'Rejected'), (b'NOTED', b'Noted as informational'), (b'RETURNED', b'Returned to preparation'), (b'REMOVED', b'Removed from agenda'), (b'TABLED', b'Tabled'), (b'ELECTION', b'Election')])),
                ('preparer', models.CharField(help_text=b'Name of the person who prepared the issue', max_length=100, null=True)),
                ('introducer', models.CharField(help_text=b'Name of the person who introduced the issue in the meeting', max_length=100, null=True)),
                ('classification_code', models.CharField(help_text=b'Classification of the item', max_length=20, null=True)),
                ('classification_description', models.CharField(help_text=b'Textual description of the item type', max_length=60, null=True)),
            ],
            options={
                'ordering': ('meeting', 'index'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.PositiveIntegerField(help_text=b'Index number of the item attachment')),
                ('name', models.CharField(help_text=b'Short name for the agenda item', max_length=400, null=True)),
                ('public', models.BooleanField(default=False, help_text=b'Is attachment public?')),
                ('file', models.FileField(null=True, upload_to=b'att')),
                ('hash', models.CharField(help_text=b'SHA-1 hash of the file contents', max_length=50, null=True)),
                ('file_type', models.CharField(help_text=b'File extension', max_length=10, null=True)),
                ('agenda_item', models.ForeignKey(to='ahjodoc.AgendaItem')),
            ],
            options={
                'ordering': ('agenda_item', 'number'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('origin_id', models.CharField(help_text=b'ID string in upstream system', unique=True, max_length=20)),
                ('name', models.CharField(help_text=b'Full category name', max_length=100, db_index=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, to='ahjodoc.Category', help_text=b'Parent category', null=True)),
            ],
            options={
                'verbose_name_plural': 'categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ContentSection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=50)),
                ('index', models.PositiveIntegerField()),
                ('text', models.TextField()),
                ('agenda_item', models.ForeignKey(to='ahjodoc.AgendaItem')),
            ],
            options={
                'ordering': ('agenda_item', 'index'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('register_id', models.CharField(help_text=b'Issue archival ID', unique=True, max_length=20, db_index=True)),
                ('slug', models.CharField(help_text=b'Unique slug (generated from register_id)', unique=True, max_length=50, db_index=True)),
                ('subject', models.CharField(help_text=b'One-line description for issue', max_length=500)),
                ('latest_decision_date', models.DateField(help_text=b'Date of the latest meeting where the issue was/will be discussed', null=True)),
                ('last_modified_time', models.DateTimeField(auto_now=True, null=True)),
                ('origin_id', models.CharField(help_text=b'ID field in the upstream source', max_length=50, null=True)),
                ('reference_text', models.TextField(null=True)),
                ('category', models.ForeignKey(help_text=b'Issue category', to='ahjodoc.Category')),
                ('districts', models.ManyToManyField(to='munigeo.District')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IssueGeometry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, db_index=True)),
                ('type', models.CharField(db_index=True, max_length=20, choices=[(b'address', b'Address'), (b'plan', b'Plan'), (b'district', b'District')])),
                ('geometry', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IssueKeyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=150, db_index=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(help_text=b'Date of the meeting', db_index=True)),
                ('number', models.PositiveIntegerField(help_text=b'Meeting number for the policymaker')),
                ('year', models.PositiveIntegerField(help_text=b'Year the meeting is held')),
                ('minutes', models.BooleanField(default=False, help_text=b'Meeting minutes document available')),
                ('issues', models.ManyToManyField(to='ahjodoc.Issue', through='ahjodoc.AgendaItem')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MeetingDocument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('origin_id', models.CharField(help_text=b'ID string in upstream system', unique=True, max_length=50)),
                ('type', models.CharField(help_text=b"Meeting document type (either 'agenda' or 'minutes')", max_length=20)),
                ('organisation', models.CharField(max_length=20)),
                ('last_modified_time', models.DateTimeField(help_text=b'Time when the meeting information last changed')),
                ('publish_time', models.DateTimeField(help_text=b'Time when the meeting document was scheduled for publishing')),
                ('origin_url', models.URLField(help_text=b'Link to the upstream file')),
                ('xml_file', models.FileField(upload_to=b'xml')),
                ('meeting', models.ForeignKey(to='ahjodoc.Meeting')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Policymaker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Name of policymaker', max_length=100)),
                ('abbreviation', models.CharField(help_text=b'Official abbreviation', max_length=20, null=True)),
                ('slug', models.CharField(help_text=b'Unique slug', max_length=50, unique=True, null=True, db_index=True)),
                ('origin_id', models.CharField(help_text=b'ID string in upstream system', max_length=20, db_index=True)),
                ('summary', models.TextField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField()),
                ('index', models.PositiveIntegerField(help_text=b'Video number within the agenda item')),
                ('start_pos', models.FloatField()),
                ('duration', models.FloatField()),
                ('speaker', models.CharField(max_length=50, null=True, db_index=True)),
                ('party', models.CharField(max_length=50, null=True)),
                ('screenshot', models.FileField(upload_to=b'video')),
                ('agenda_item', models.ForeignKey(to='ahjodoc.AgendaItem', null=True)),
                ('meeting', models.ForeignKey(to='ahjodoc.Meeting')),
            ],
            options={
                'ordering': ('agenda_item', 'start_pos'),
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='video',
            unique_together=set([('meeting', 'agenda_item', 'start_pos')]),
        ),
        migrations.AddField(
            model_name='meeting',
            name='policymaker',
            field=models.ForeignKey(help_text=b'Policymaker or other organization', to='ahjodoc.Policymaker'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='meeting',
            unique_together=set([('policymaker', 'year', 'number')]),
        ),
        migrations.AlterUniqueTogether(
            name='issuegeometry',
            unique_together=set([('name', 'type')]),
        ),
        migrations.AddField(
            model_name='issue',
            name='geometries',
            field=models.ManyToManyField(to='ahjodoc.IssueGeometry'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issue',
            name='keywords',
            field=models.ManyToManyField(to='ahjodoc.IssueKeyword'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='contentsection',
            unique_together=set([('agenda_item', 'index')]),
        ),
        migrations.AlterUniqueTogether(
            name='attachment',
            unique_together=set([('agenda_item', 'number')]),
        ),
        migrations.AddField(
            model_name='agendaitem',
            name='issue',
            field=models.ForeignKey(help_text=b'Issue for the item', to='ahjodoc.Issue'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='agendaitem',
            name='meeting',
            field=models.ForeignKey(help_text=b'Meeting for the agenda item', to='ahjodoc.Meeting'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='agendaitem',
            unique_together=set([('meeting', 'issue'), ('meeting', 'index')]),
        ),
    ]
