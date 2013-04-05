# -*- coding: utf-8 -*-

import os
import logging
import datetime
from optparse import make_option
from django.core.management.base import BaseCommand
from django import db
from django.conf import settings

from ahjodoc.scanner import AhjoScanner
from ahjodoc.doc import AhjoDocument
from ahjodoc.models import *

#parser.add_argument('--config', dest='config', action='store', help='config file location (YAML format)')
#parser.add_argument()

class Command(BaseCommand):
    help = "Import OpenAHJO documents"
    option_list = BaseCommand.option_list + (
        make_option('--cached', dest='cached', action='store_true', help='cache HTTP requests'),
        make_option('--meeting-id', dest='meeting_id', action='store', help='import one meeting'),
    )

    def import_doc(self, info):
        origin_id = info['origin_id']
        try:
            doc = MeetingDocument.objects.get(origin_id=origin_id)
        except MeetingDocument.DoesNotExist:
            print "Adding new document %s" % origin_id
            doc = MeetingDocument(origin_id=origin_id)
        doc.organisation = info['org']
        doc.committee = info['committee']
        d = [int(x) for x in info['date'].split('-')]
        doc.date = datetime.date(*d)
        doc.meeting_nr = info['meeting_nr']
        doc.origin_url = info['url']

        adoc = AhjoDocument()
        zipf = self.scanner.download_document(info)
        adoc.import_from_zip(zipf)
        zipf.close()
        fname = info['origin_id'] + '.xml'
        print "Storing cleaned XML to %s" % fname
        xmlf = open(os.path.join(self.xml_path, fname), 'w')
        doc.type = adoc.type
        if doc.type == 'agenda':
            assert info['doc_type'] == 'El'
        elif doc.type == 'minutes':
            assert info['doc_type'] == 'Pk'
        adoc.output_cleaned_xml(xmlf)
        xmlf.close()
        doc.xml_file = os.path.join(settings.AHJO_XML_PATH, fname)
        doc.publish_time = adoc.publish_time
        doc.last_modified_time = info['last_modified']
        doc.save()

    def handle(self, **options):
        self.scanner = AhjoScanner()
        doc_list = self.scanner.scan_documents(cached=options['cached'])
        media_dir = settings.MEDIA_ROOT
        self.scanner.doc_store_path = os.path.join(media_dir, settings.AHJO_ZIP_PATH)
        self.xml_path = os.path.join(media_dir, settings.AHJO_XML_PATH)
        try:
            os.makedirs(self.xml_path)
        except OSError:
            pass
        if options['meeting_id']:
            for info in doc_list:
                if info['origin_id'] == options['meeting_id']:
                    self.import_doc(info)
                    break
            else:
                print "No meeting document with id '%s' found" % options['meeting_id']
                exit(1)
        else:
            for info in doc_list:
                self.import_doc(info)
