#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import os
import re
import logging
import cPickle
from noaho import NoAho
from django.contrib.gis.gdal import DataSource, SpatialReference, CoordTransform
from django.contrib.gis.geos import GEOSGeometry, Point, Polygon, MultiPolygon, LineString, LinearRing
from django.conf import settings

GK25_SRID = 3879

class AhjoGeocoder(object):
    PLAN_UNIT_SHORT_MATCH = r'^(\d{3,5})/(\d+)(.*)$'
    PLAN_UNIT_LONG_MATCH = r'^0?91-(\d+)-(\d+)-(\d+)(.*)$'

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.no_match_addresses = []
        self.no_match_plans = []
        self.no_match_plan_units = []
        self.plan_map = {}
        self.plan_unit_map = {}
        self.property_map = {}
        self.street_tree = None
        self.matches = 0

    def convert_from_gk25(self, north, east):
        pnt = Point(east, north, srid=GK25_SRID)
        pnt.transform(settings.PROJECTION_SRID)
        return pnt

    def geocode_address(self, text):
        if not self.street_tree:
            return {}

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

            e_list = self.street_hash[street_name]
            for e in e_list:
                if num == e['num']:
                    break
                if e['num_end'] and e['num'] < num <= e['num_end']:
                    break
            else:
                self.logger.warning("No match found for '%s %d'" % (street_name, num))
                s = '%s %d' % (e['street'], num)
                if not s in self.no_match_addresses:
                    self.no_match_addresses.append(s)
                continue

            pnt = self.convert_from_gk25(e['coord_n'], e['coord_e'])
            geom = {'name': '%s %d' % (e['street'], num), 'geometry': pnt, 'type': 'address'}
            geom_id = "%s/%s" % (geom['type'], geom['name'])
            geometries[geom_id] = geom
        return geometries

    def geocode_plan(self, plan_id):
        plan = self.plan_map.get(plan_id)
        if not plan:
            if plan_id not in self.no_match_plans:
                self.logger.warning("No plan found for plan id %s" % plan_id)
                self.no_match_plans.append(plan_id)
            return
        return {'name': plan_id, 'geometry': plan['geometry'], 'type': 'plan'}

    def geocode_plan_unit(self, text, context):
        # If there are more than one '/' characters, it's not a plan unit
        m = re.match(self.PLAN_UNIT_SHORT_MATCH, text)
        if m:
            if text.count('/') > 1:
                return None
            block_id, unit_id, rest = m.groups()
            block_id = int(block_id)
            unit_id = int(unit_id)
            district_id = block_id // 1000
            block_id %= 1000
            if rest:
                if rest[0].lower() in ('a', 'b', 'c', 'd', 'e'):
                    rest = rest[1:]
                rest = rest.strip()
                if rest and rest[0] == '-':
                    range_end = int(re.match('-\s?(\d)+', rest).groups()[0])
                elif rest.startswith('ja'):
                    range_end = int(rest[2:])
                elif rest.lower().startswith('.a'): # Ksv notation
                    pass
                elif rest.startswith(':'): # ???
                    pass
            # check for '161/3.A' style
            if not district_id:
                for l in context['all_text']:
                    m = re.match(r'(\d+)\.ko', l, re.I)
                    if not m:
                        continue
                    district_id = int(m.groups()[0])
                    break
                if not district_id:
                    self.logger.warning("No district id found for '%s'" % text)
                    return None
        else:
            m = re.match(self.PLAN_UNIT_LONG_MATCH, text)
            district_id, block_id, unit_id = [int(x) for x in m.groups()[0:3]]
            rest = m.groups()[3]

        jhs_id = '091%03d%04d%04d' % (district_id, block_id, unit_id)
        name = '91-%d-%d-%d' % (district_id, block_id, unit_id)
        plan_unit = self.plan_unit_map.get(jhs_id, None)
        prop = self.property_map.get(jhs_id, None)
        geometry = None
        if plan_unit:
            geometry = plan_unit['geometry']
        elif prop:
            geometry = prop['geometry']
        else:
            print("No geometry found for '%s'" % jhs_id)
            self.logger.warning("No geometry found for '%s'" % jhs_id)
            self.no_match_plan_units.append([text, jhs_id])
            return None

        self.matches += 1
        return {'name': name, 'type': 'plan_unit', 'geometry': geometry}

    def geocode_district(self, text):
        return

    def geocode_from_text(self, text, context):
        text = text.strip()
        if not isinstance(text, unicode):
            text = unicode(text)

        geometries = {}

        # Check for plan unit IDs
        m1 = re.match(self.PLAN_UNIT_SHORT_MATCH, text)
        m2 = re.match(self.PLAN_UNIT_LONG_MATCH, text)
        if m1 or m2:
            geom = self.geocode_plan_unit(text, context)
            if geom:
                geom_id = "%s/%s" % (geom['type'], geom['name'])
                geometries[geom_id] = geom
            return geometries

        m = re.match(r'^(\d{3,5})\.[pP]$', text)
        if m:
            geom = self.geocode_plan(m.groups()[0])
            if geom:
                geom_id = "%s/%s" % (geom['type'], geom['name'])
                geometries[geom_id] = geom

        geometries.update(self.geocode_address(text))

        return geometries

    def geocode_from_text_list(self, text_list):
        geometries = {}
        context = {'all_text': text_list}
        for text in text_list:
            g = self.geocode_from_text(text, context)
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
            if plan['geometry']:
                if isinstance(plan['geometry'], Polygon):
                    plan['geometry'] = MultiPolygon(plan['geometry'])
                plan['geometry'].append(poly)
            else:
                plan['geometry'] = poly
        print "%d plans imported" % idx

    def load_plan_units(self, plan_unit_file):
        try:
            picklef = open('plan_units.pickle', 'r')
            self.plan_unit_map = cPickle.load(picklef)
            print "%d plan units loaded" % len(self.plan_unit_map)
            return
        except IOError:
            pass

        ds = DataSource(plan_unit_file, encoding='iso8859-1')
        lyr = ds[0]

        for idx, feat in enumerate(lyr):
            origin_id = feat['jhstunnus'].as_string().strip()
            geom = feat.geom
            geom.srid = GK25_SRID
            geom.transform(settings.PROJECTION_SRID)
            if origin_id not in self.plan_unit_map:
                plan = {'geometry': None}
                self.plan_unit_map[origin_id] = plan
            else:
                plan = self.plan_unit_map[origin_id]
            poly = GEOSGeometry(geom.wkb, srid=geom.srid)
            if isinstance(poly, LineString):
                try:
                    ring = LinearRing(poly.tuple)
                except Exception:
                    self.logger.error("Skipping plan %s, it's linestring doesn't close." % origin_id)
                    # if the LineString doesn't form a polygon, skip it.
                    continue
                poly = Polygon(ring)
            if plan['geometry']:
                if isinstance(plan['geometry'], Polygon):
                    plan['geometry'] = MultiPolygon(plan['geometry'])
                if isinstance(poly, MultiPolygon):
                    plan['geometry'].extend(poly)
                else:
                    plan['geometry'].append(poly)
            else:
                plan['geometry'] = poly
        print "%d plan units imported" % idx

        for key in self.plan_unit_map.keys():
            geom = self.plan_unit_map[key]['geometry']
            if not geom.valid:
                self.logger.warning("geometry for %s not OK, fixing" % key)
                geom = geom.simplify()
                assert geom.valid
                self.plan_unit_map[key]['geometry'] = geom

        picklef = open('plan_units.pickle', 'w')
        cPickle.dump(self.plan_unit_map, picklef)

    def load_properties(self, property_file):
        try:
            picklef = open('geo_properties.pickle', 'r')
            self.property_map = cPickle.load(picklef)
            print "%d properties loaded" % len(self.property_map)
            return
        except IOError:
            pass

        f = open(property_file, 'r')
        reader = csv.reader(f)
        header = reader.next()

        ident_row = header.index('estx_ident')
        x_row = header.index('estx_ixm')
        y_row = header.index('estx_iym')
        name_row = header.index('estx_enam')

        self.property_map = {}
        for idx, row in enumerate(reader):
            x, y = row[x_row], row[y_row]
            # Discard rows without coordinates
            if not x or not y:
                continue
            x = int(x)
            y = int(y)
            if not x or not y:
                continue

            s = row[ident_row]
            origin_id = s
            assert origin_id not in self.property_map
            pnt = self.convert_from_gk25(y, x)
            self.property_map[origin_id] = {'geometry': pnt}
        print "%d properties imported" % idx

        picklef = open('geo_properties.pickle', 'w')
        cPickle.dump(self.property_map, picklef)
