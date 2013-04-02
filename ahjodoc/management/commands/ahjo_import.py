# -*- coding: utf-8 -*-

import os
import logging
import datetime
from django.core.management.base import BaseCommand
from django import db
from django.conf import settings

from ahjodoc.scanner import AhjoScanner
from ahjodoc.doc import AhjoDocument
from ahjodoc.models import *

#parser.add_argument('--config', dest='config', action='store', help='config file location (YAML format)')
#parser.add_argument('--cached', dest='cached', action='store_true', help='cache HTTP requests')

class Command(BaseCommand):
    help = "Import OpenAHJO documents"

    def handle(self, **options):
        scanner = AhjoScanner()
        doc_list = scanner.scan_documents(cached=False)
        static_dir = settings.STATIC_ROOT
        scanner.doc_store_path = os.path.join(static_dir, 'zip')
        xml_dir = os.path.join(static_dir, 'xml')
        try:
            os.makedirs(xml_dir)
        except OSError:
            pass
        for info in doc_list:
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
            doc.save()

            adoc = AhjoDocument()
            zipf = scanner.download_document(info)
            adoc.import_from_zip(zipf)
            zipf.close()
            fname = os.path.join(xml_dir, info['origin_id'] + '.xml')
            print "Storing cleaned XML to %s" % fname
            xmlf = open(fname, 'w')
            adoc.output_cleaned_xml(xmlf)
            xmlf.close()
