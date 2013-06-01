# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Committee'
        db.create_table(u'ahjodoc_committee', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('abbreviation', self.gf('django.db.models.fields.CharField')(max_length=20, null=True)),
            ('origin_id', self.gf('django.db.models.fields.CharField')(max_length=20, db_index=True)),
        ))
        db.send_create_signal(u'ahjodoc', ['Committee'])

        # Adding model 'Meeting'
        db.create_table(u'ahjodoc_meeting', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('committee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ahjodoc.Committee'])),
            ('date', self.gf('django.db.models.fields.DateField')(db_index=True)),
            ('number', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('year', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('minutes', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'ahjodoc', ['Meeting'])

        # Adding unique constraint on 'Meeting', fields ['committee', 'date']
        db.create_unique(u'ahjodoc_meeting', ['committee_id', 'date'])

        # Adding unique constraint on 'Meeting', fields ['committee', 'year', 'number']
        db.create_unique(u'ahjodoc_meeting', ['committee_id', 'year', 'number'])

        # Adding model 'MeetingDocument'
        db.create_table(u'ahjodoc_meetingdocument', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('meeting', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ahjodoc.Meeting'])),
            ('origin_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('organisation', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('last_modified_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('publish_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('origin_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('xml_file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal(u'ahjodoc', ['MeetingDocument'])

        # Adding model 'Category'
        db.create_table(u'ahjodoc_category', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('origin_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('parent', self.gf('mptt.fields.TreeForeignKey')(to=orm['ahjodoc.Category'], null=True, blank=True)),
            ('lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal(u'ahjodoc', ['Category'])

        # Adding model 'Issue'
        db.create_table(u'ahjodoc_issue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('register_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20, db_index=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ahjodoc.Category'])),
        ))
        db.send_create_signal(u'ahjodoc', ['Issue'])

        # Adding model 'IssueGeometry'
        db.create_table(u'ahjodoc_issuegeometry', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('issue', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ahjodoc.Issue'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.GeometryField')()),
        ))
        db.send_create_signal(u'ahjodoc', ['IssueGeometry'])

        # Adding model 'AgendaItem'
        db.create_table(u'ahjodoc_agendaitem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('meeting', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ahjodoc.Meeting'])),
            ('issue', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ahjodoc.Issue'])),
            ('index', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('from_minutes', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('last_modified_time', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
        ))
        db.send_create_signal(u'ahjodoc', ['AgendaItem'])

        # Adding unique constraint on 'AgendaItem', fields ['meeting', 'issue']
        db.create_unique(u'ahjodoc_agendaitem', ['meeting_id', 'issue_id'])

        # Adding unique constraint on 'AgendaItem', fields ['meeting', 'index']
        db.create_unique(u'ahjodoc_agendaitem', ['meeting_id', 'index'])

        # Adding model 'Attachment'
        db.create_table(u'ahjodoc_attachment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('agenda_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ahjodoc.AgendaItem'])),
            ('number', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True)),
            ('hash', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('file_type', self.gf('django.db.models.fields.CharField')(max_length=10, null=True)),
        ))
        db.send_create_signal(u'ahjodoc', ['Attachment'])

        # Adding unique constraint on 'Attachment', fields ['agenda_item', 'number']
        db.create_unique(u'ahjodoc_attachment', ['agenda_item_id', 'number'])

        # Adding model 'ContentSection'
        db.create_table(u'ahjodoc_contentsection', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('agenda_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ahjodoc.AgendaItem'])),
            ('index', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'ahjodoc', ['ContentSection'])

        # Adding unique constraint on 'ContentSection', fields ['agenda_item', 'index']
        db.create_unique(u'ahjodoc_contentsection', ['agenda_item_id', 'index'])


    def backwards(self, orm):
        # Removing unique constraint on 'ContentSection', fields ['agenda_item', 'index']
        db.delete_unique(u'ahjodoc_contentsection', ['agenda_item_id', 'index'])

        # Removing unique constraint on 'Attachment', fields ['agenda_item', 'number']
        db.delete_unique(u'ahjodoc_attachment', ['agenda_item_id', 'number'])

        # Removing unique constraint on 'AgendaItem', fields ['meeting', 'index']
        db.delete_unique(u'ahjodoc_agendaitem', ['meeting_id', 'index'])

        # Removing unique constraint on 'AgendaItem', fields ['meeting', 'issue']
        db.delete_unique(u'ahjodoc_agendaitem', ['meeting_id', 'issue_id'])

        # Removing unique constraint on 'Meeting', fields ['committee', 'year', 'number']
        db.delete_unique(u'ahjodoc_meeting', ['committee_id', 'year', 'number'])

        # Removing unique constraint on 'Meeting', fields ['committee', 'date']
        db.delete_unique(u'ahjodoc_meeting', ['committee_id', 'date'])

        # Deleting model 'Committee'
        db.delete_table(u'ahjodoc_committee')

        # Deleting model 'Meeting'
        db.delete_table(u'ahjodoc_meeting')

        # Deleting model 'MeetingDocument'
        db.delete_table(u'ahjodoc_meetingdocument')

        # Deleting model 'Category'
        db.delete_table(u'ahjodoc_category')

        # Deleting model 'Issue'
        db.delete_table(u'ahjodoc_issue')

        # Deleting model 'IssueGeometry'
        db.delete_table(u'ahjodoc_issuegeometry')

        # Deleting model 'AgendaItem'
        db.delete_table(u'ahjodoc_agendaitem')

        # Deleting model 'Attachment'
        db.delete_table(u'ahjodoc_attachment')

        # Deleting model 'ContentSection'
        db.delete_table(u'ahjodoc_contentsection')


    models = {
        u'ahjodoc.agendaitem': {
            'Meta': {'ordering': "('meeting', 'index')", 'unique_together': "(('meeting', 'issue'), ('meeting', 'index'))", 'object_name': 'AgendaItem'},
            'from_minutes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'issue': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ahjodoc.Issue']"}),
            'last_modified_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'meeting': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ahjodoc.Meeting']"})
        },
        u'ahjodoc.attachment': {
            'Meta': {'ordering': "('agenda_item', 'number')", 'unique_together': "(('agenda_item', 'number'),)", 'object_name': 'Attachment'},
            'agenda_item': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ahjodoc.AgendaItem']"}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True'}),
            'file_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'ahjodoc.category': {
            'Meta': {'object_name': 'Category'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'to': u"orm['ahjodoc.Category']", 'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        u'ahjodoc.committee': {
            'Meta': {'object_name': 'Committee'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'})
        },
        u'ahjodoc.contentsection': {
            'Meta': {'ordering': "('agenda_item', 'index')", 'unique_together': "(('agenda_item', 'index'),)", 'object_name': 'ContentSection'},
            'agenda_item': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ahjodoc.AgendaItem']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'ahjodoc.issue': {
            'Meta': {'object_name': 'Issue'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ahjodoc.Category']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'register_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        u'ahjodoc.issuegeometry': {
            'Meta': {'object_name': 'IssueGeometry'},
            'geometry': ('django.contrib.gis.db.models.fields.GeometryField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ahjodoc.Issue']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'ahjodoc.meeting': {
            'Meta': {'unique_together': "(('committee', 'date'), ('committee', 'year', 'number'))", 'object_name': 'Meeting'},
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ahjodoc.Committee']"}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issues': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['ahjodoc.Issue']", 'through': u"orm['ahjodoc.AgendaItem']", 'symmetrical': 'False'}),
            'minutes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'ahjodoc.meetingdocument': {
            'Meta': {'object_name': 'MeetingDocument'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_time': ('django.db.models.fields.DateTimeField', [], {}),
            'meeting': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ahjodoc.Meeting']"}),
            'organisation': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'origin_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'publish_time': ('django.db.models.fields.DateTimeField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'xml_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['ahjodoc']