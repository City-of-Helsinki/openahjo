#!/usr/bin/env python
import csv
import os
import re
import logging
from noaho import NoAho
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.geos import Point
from django.conf import settings

class AhjoGeocoder(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.no_match_addresses = []

    def convert_from_gk25(self, north, east):
        pnt = Point(east, north, srid=3879)
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
            self.no_match_addresses.append('%s %d' % (e['street'], num))
            return None

        pnt = self.convert_from_gk25(e['coord_n'], e['coord_e'])
        return {'name': '%s %d' % (e['street'], num), 'location': pnt}

    def geocode_from_text(self, text):
        if not isinstance(text, unicode):
            text = unicode(text)
        textl = text.lower()
        ret = [x for x in self.street_tree.findall_long(textl)]
        points = {}
        for street_match in ret:
            (start, end) = street_match[0:2]
            street_name = textl[start:end]
            # check for the address number
            m = re.match(r'\s*(\d+)', text[end:])
            if not m:
                #print "\tno address: %s" % text[start:]
                continue
            num = int(m.groups()[0])

            print "\t%s %d" % (street_name, num)
            pnt = self.geocode_address(street_name, num)
            if pnt:
                points[pnt['name']] = pnt
        return points

    def geocode_from_text_list(self, text_list):
        points = {}
        for text in text_list:
            p = self.geocode_from_text(text)
            points.update(p)
        return [pnt for name, pnt in points.iteritems()]

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
