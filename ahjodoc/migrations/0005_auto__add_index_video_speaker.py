# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'Video', fields ['speaker']
        db.create_index(u'ahjodoc_video', ['speaker'])


    def backwards(self, orm):
        # Removing index on 'Video', fields ['speaker']
        db.delete_index(u'ahjodoc_video', ['speaker'])


    models = {
        u'ahjodoc.agendaitem': {
            'Meta': {'ordering': "('meeting', 'index')", 'unique_together': "(('meeting', 'issue'), ('meeting', 'index'))", 'object_name': 'AgendaItem'},
            'from_minutes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'issue': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ahjodoc.Issue']"}),
            'last_modified_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'meeting': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ahjodoc.Meeting']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '500'})
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
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
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
        },
        u'ahjodoc.video': {
            'Meta': {'ordering': "('agenda_item', 'start_pos')", 'unique_together': "(('meeting', 'agenda_item', 'start_pos'),)", 'object_name': 'Video'},
            'agenda_item': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ahjodoc.AgendaItem']", 'null': 'True'}),
            'duration': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'meeting': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ahjodoc.Meeting']"}),
            'party': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'screenshot': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'speaker': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'db_index': 'True'}),
            'start_pos': ('django.db.models.fields.FloatField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['ahjodoc']