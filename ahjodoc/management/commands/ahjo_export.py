# -*- coding: utf-8 -*-

import os
import sys
import logging
import json

from collections import OrderedDict

import ogr
import osr
from optparse import make_option
from django.core.management.base import BaseCommand
from django.contrib.gis.gdal.error import OGRException, check_err
from django.contrib.gis.geos import Point, Polygon, MultiPolygon
from django import db
from django.conf import settings
from ahjodoc.models import *

TARGET_CRS='EPSG:3879'  # ETRS-GK25

class Command(BaseCommand):
    help = "Export OpenAHJO data"
    option_list = BaseCommand.option_list + (
        #make_option('--cached', dest='cached', action='store_true', help='cache HTTP requests'),
        make_option('--output', dest='output', help='output filename'),
    )

    def output_mapinfo(self):
        drv_name = "MapInfo File"
        drv = ogr.GetDriverByName(drv_name)
        if drv is None:
            raise OGRException("%s driver not available" % drv)
        if not options['output']:
            raise Exception("Must supply output filename")
        ds = drv.CreateDataSource(options['output'])
        if ds is None:
            raise OGRException("Failed to output to '%s'" % options['output'])
        srs = osr.SpatialReference()
        check_err(srs.SetFromUserInput(TARGET_CRS))

        lyr = ds.CreateLayer('paatos', srs, ogr.wkbPoint)
        if lyr is None:
            raise OGRException("Layer creation failed")

        field_def = ogr.FieldDefn("diaarinro", ogr.OFTString)
        field_def.SetWidth(20)
        check_err(lyr.CreateField(field_def))

        field_def = ogr.FieldDefn("otsikko", ogr.OFTString)
        field_def.SetWidth(100)
        check_err(lyr.CreateField(field_def))

        field_def = ogr.FieldDefn("openahjo", ogr.OFTString)
        field_def.SetWidth(100)
        check_err(lyr.CreateField(field_def))

        issue_list = Issue.objects.filter(geometries__isnull=False)
        for issue in issue_list:
            print issue
            geom_list = issue.geometries.all()
            pnt = None
            for geom in geom_list:
                g = geom.geometry
                if not isinstance(g, Point):
                    pnt = g.centroid
                else:
                    pnt = g
                break
            pnt.transform(TARGET_CRS)

            feat = ogr.Feature(lyr.GetLayerDefn())
            feat.SetField("diaarinro", issue.register_id.encode('utf8'))
            feat.SetField("otsikko", issue.subject.encode('utf8'))
            feat.SetField("openahjo", "http://dev.hel.fi/paatokset/asia/%s/" % issue.slug.encode('utf8'))

            pt = ogr.Geometry(ogr.wkbPoint)
            pt.SetPoint_2D(0, pnt.x, pnt.y)
            feat.SetGeometry(pt)

            check_err(lyr.CreateFeature(feat))
            feat.Destroy()

    def output_geojson(self):
        agenda_item_list = AgendaItem.objects.filter(issue__geometries__isnull=False).select_related('issue')
        features = []
        for ai in agenda_item_list:
            issue = ai.issue
            geom_list = issue.geometries.all()
            for geom in geom_list:
                g = geom.geometry
                break
            geometry = json.loads(g.geojson)
            meeting = ai.meeting
            origin_id = issue.origin_id
            if not origin_id:
                origin_id = ''
            view_url = "http://dev.hel.fi/openahjo/issue/%s/%s-%d-%d/" % (issue.slug.encode('utf8'),
                    meeting.policymaker.slug, meeting.year, meeting.number)
            props = [('id', ai.id), ('register_id', issue.register_id), ('subject', ai.subject),
                     ('policymaker', meeting.policymaker.abbreviation), ('meeting_date', str(meeting.date)),
                     ('meeting_id', "%d/%d" % (meeting.number, meeting.year)),
                     ('preparer', ai.preparer), ('introducer', ai.introducer),
                     ('geometry_type', geom.type), ('geometry_name', geom.name),
                     ('view_url', view_url), ('origin_id', origin_id)]

            feat = {'type': 'Feature', 'properties': OrderedDict(props), 'geometry': geometry}
            features.append(feat)
        fc = {'type': 'FeatureCollection', 'features': features}
        f = open(self.options['output'], 'w')
        f.write(json.dumps(fc, indent=4))
        f.close()

    def handle(self, **options):
        self.logger = logging.getLogger(__name__)
        self.data_path = os.path.join(settings.PROJECT_ROOT, 'data')

        self.options = options
        self.output_geojson()
