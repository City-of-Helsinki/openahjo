#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import os
import re
import logging
from noaho import NoAho
from django.contrib.gis.gdal import DataSource, SpatialReference, CoordTransform
from django.contrib.gis.geos import GEOSGeometry, Point, Polygon, MultiPolygon, LineString, LinearRing
from django.conf import settings

GK25_SRID = 3879

class AhjoGeocoder(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.no_match_addresses = []
        self.no_match_plans = []
        self.plan_map = {}

    def convert_from_gk25(self, north, east):
        pnt = Point(east, north, srid=GK25_SRID)
        pnt.transform(settings.PROJECTION_SRID)
        return pnt

    def geocode_address(self, street, num):
        e_list = self.street_hash[street]
        for e in e_list:
            if num == e['num']:
                break
            if e['num_end'] and e['num'] < num <= e['num_end']:
                break
        else:
            self.logger.warning("No match found for '%s %d'" % (street, num))
            s = '%s %d' % (e['street'], num)
            if not s in self.no_match_addresses:
                self.no_match_addresses.append(s)
            return None

        pnt = self.convert_from_gk25(e['coord_n'], e['coord_e'])
        return {'name': '%s %d' % (e['street'], num), 'geometry': pnt, 'type': 'address'}

    def geocode_plan(self, plan_id):
        plan = self.plan_map.get(plan_id)
        if not plan:
            if plan_id not in self.no_match_plans:
                self.logger.warning("No plan found for plan id %s" % plan_id)
                self.no_match_plans.append(plan_id)
            return
        return {'name': plan_id, 'geometry': plan['geometry'], 'type': 'plan'}

    def geocode_district(self, text):
        return

    def geocode_from_text(self, text):
        if not isinstance(text, unicode):
            text = unicode(text).strip()
        STREET_SUFFIXES = ('katu', 'tie', 'kuja', 'polku', 'kaari', 'linja', 'raitti', 'rinne', 'penger', 'ranta', u'väylä')
        for sfx in STREET_SUFFIXES:
            m = re.search(r'([A-Z]\w+%s)\s+(\d+)' % sfx, text)
            if not m:
                continue
            street_name = m.groups()[0].lower()
            if not street_name in self.street_hash:
                print "Street name not found: %s" % street_name
                self.no_match_addresses.append('%s %s' % (m.groups()[0], m.groups()[1]))
        textl = text.lower()
        ret = [x for x in self.street_tree.findall_long(textl)]
        geometries = {}
        for street_match in ret:
            (start, end) = street_match[0:2]
            street_name = textl[start:end]
            # check for the address number
            m = re.match(r'\s*(\d+)', text[end:])
            if not m:
                #print "\tno address: %s" % text[start:]
                continue
            num = int(m.groups()[0])

            geom = self.geocode_address(street_name, num)
            if geom:
                geom_id = "%s/%s" % (geom['type'], geom['name'])
                geometries[geom_id] = geom

        m = re.match(r'^(\d{3,5})\.[a-zA-Z]$', text)
        if m:
            geom = self.geocode_plan(m.groups()[0])
            if geom:
                geom_id = "%s/%s" % (geom['type'], geom['name'])
                geometries[geom_id] = geom

        return geometries

    def geocode_from_text_list(self, text_list):
        geometries = {}
        for text in text_list:
            g = self.geocode_from_text(text)
            geometries.update(g)
        return [geom for geom_id, geom in geometries.iteritems()]

    def load_address_database(self, csv_file):
        reader = csv.reader(csv_file, delimiter=',')
        reader.next()
        addr_hash = {}
        for idx, row in enumerate(reader):
            row_type = int(row[-1])
            if row_type != 1:
                continue
            street = row[0].strip()
            if not row[1]:
                continue
            num = int(row[1])
            if not num:
                continue
            num2 = row[2]
            if not num2:
                num2 = None
            letter = row[3]
            muni_name = row[10]
            coord_n = int(row[8])
            coord_e = int(row[9])
            if muni_name != "Helsinki":
                continue
            e = {'muni': muni_name, 'street': street, 'num': num, 'num_end': num2,
                 'letter': letter, 'coord_n': coord_n, 'coord_e': coord_e}
            street = street.lower().decode('utf8')
            if street in addr_hash:
                if num2 == None:
                    num2s = ''
                else:
                    num2s = str(num2)
                addr_hash[street].append(e)
            else:
                addr_hash[street] = [e]
        self.street_hash = addr_hash
        self.street_tree = NoAho()
        print "%d street names loaded" % len(self.street_hash)
        for street in self.street_hash.keys():
            self.street_tree.add(street)

    def load_plans(self, plan_file):
        ds = DataSource(plan_file, encoding='iso8859-1')
        lyr = ds[0]

        for idx, feat in enumerate(lyr):
            origin_id = feat['kaavatunnus'].as_string().strip()
            geom = feat.geom
            geom.srid = GK25_SRID
            geom.transform(settings.PROJECTION_SRID)
            if origin_id not in self.plan_map:
                plan = {'geometry': None}
                self.plan_map[origin_id] = plan
            else:
                plan = self.plan_map[origin_id]
            poly = GEOSGeometry(geom.wkb, srid=geom.srid)
            if isinstance(poly, LineString):
                try:
                    ring = LinearRing(poly.tuple)
                except Exception:
                    self.logger.error("Skipping plan %s, it's linestring doesn't close." % origin_id)
                    # if the LineString doesn't form a polygon, skip it.
                    continue
                poly = Polygon(ring)
                print type(poly)
            if plan['geometry']:
                if isinstance(plan['geometry'], Polygon):
                    plan['geometry'] = MultiPolygon(plan['geometry'])
                plan['geometry'].append(poly)
            else:
                plan['geometry'] = poly
        print "%d plans imported" % idx
