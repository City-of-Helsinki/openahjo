#!/usr/bin/env python

import argparse
import yaml
import mongoengine
import collections
import datetime

from scanner import AhjoScanner
from doc import AhjoDocument
from models import ZipDocument

parser = argparse.ArgumentParser(description='Import OpenAHJO documents.')
parser.add_argument('--config', dest='config', action='store', help='config file location (YAML format)')

args = parser.parse_args()

def update_config(d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d

config = {
    'mongo': {'db': 'openahjo'}
}

if args.config:
    config = yaml.load(open(args.config, 'r'))

mongoengine.connect(config['mongo']['db'])

scanner = AhjoScanner()
doc_list = scanner.scan_documents()

for info in doc_list:
    origin_id = info['origin_id']
    try:
        doc = ZipDocument.objects.get(origin_id=origin_id)
    except ZipDocument.DoesNotExist:
        print "Adding new document %s" % origin_id
        doc = ZipDocument(origin_id=origin_id)
    doc.organisation = info['org']
    doc.committee = info['committee']
    d = [int(x) for x in info['date'].split('-')]
    doc.date = datetime.date(*d)
    doc.meeting_nr = info['meeting_nr']
    doc.url = info['url']
    doc.save()
