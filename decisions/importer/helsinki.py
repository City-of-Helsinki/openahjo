# -*- coding: utf-8 -*-
import os
import json
import re
from dateutil.parser import parse as dateutil_parse
from pprint import pprint

from django.conf import settings
from django.utils.text import slugify
from .sync import ModelSyncher
from .base import Importer, register_importer

from decisions.models import *

TYPE_MAP = {
    1: 'council',
    2: 'board',
    4: 'board_division',
    5: 'committee',
    7: 'field',
    8: 'department',
    9: 'division',
    10: 'introducer',
    11: 'introducer_field',
    12: 'office_holder',
    13: 'city',
    14: 'unit',
}

TYPE_NAME_FI = {
    1:  'Valtuusto',
    2:  'Hallitus',
    3:  'Johtajisto',
    4:  'Jaosto',
    5:  'Lautakunta',
    6:  'Yleinen',
    7:  'Toimiala',
    8:  'Virasto',
    9:  'Osasto',
    10: 'Esittelijä',
    11: 'Esittelijä (toimiala)',
    12: 'Viranhaltija',
    13: 'Kaupunki',
    14: 'Yksikkö',
}

def mark_deleted(obj):
    if obj.deleted:
        return False
    obj.deleted = True
    obj.save(update_fields=['deleted'])
    return True

def origin_id_to_id(origin_id):
    return 'hel:%s' % origin_id

@register_importer
class HelsinkiImporter(Importer):
    name = 'helsinki'

    def setup(self):
        pass

    def _import_organization(self, info):
        if info['type'] not in TYPE_MAP:
            return
        org = {'origin_id': info['id']}
        org['id'] = origin_id_to_id(org['origin_id'])
        org['type'] = TYPE_MAP[info['type']]

        if org['type'] in ['introducer', 'introducer_field']:
            self.skip_orgs.add(org['origin_id'])
            return

        org['name'] = {'fi': info['name_fin'], 'sv': info['name_swe']}
        if info['shortname']:
            org['abbreviation'] = info['shortname']

        # FIXME: Use maybe sometime
        DUPLICATE_ABBREVS = [
            'AoOp', 'Vakaj', 'Talk', 'KIT', 'HTA', 'Ryj', 'Pj', 'Sotep', 'Hp', 
            'Kesvlk siht', 'Kulttj', 'HVI', 'Sostap', 'KOT',
            'Lsp', 'Kj', 'KYT', 'AST', 'Sote', 'Vp', 'HHE', 'Tj', 'HAKE', 'Ko'
        ]

        abbr = org.get('abbreviation', None)
        if org['type'] in ('council', 'committee', 'board_division', 'board'):
            org['slug'] = slugify(org['abbreviation'])
        else:
            org['slug'] = slugify(org['origin_id'])

        org['founding_date'] = None
        if info['start_time']:
            d = dateutil_parse(info['start_time'])
            # 2009-01-01 means "no data"
            if not (d.year == 2009 and d.month == 1 and d.day == 1):
                org['founding_date'] = d.date().strftime('%Y-%m-%d')

        org['dissolution_date'] = None
        if info['end_time']:
            d = dateutil_parse(info['end_time'])
            org['dissolution_date'] = d.date().strftime('%Y-%m-%d')

        org['contact_details'] = []
        if info['visitaddress_street'] or info['visitaddress_zip']:
            cd = {'type': 'address'}
            cd['value'] = info.get('visitaddress_street', '')
            z = info.get('visitaddress_zip', '')
            if z and len(z) == 2:
                z = "00%s0" % z
            cd['postcode'] = z
            org['contact_details'].append(cd)
        org['modified_at'] = dateutil_parse(info['modified_time'])

        parents = info['parents']
        if parents == None:
            parents = []
        org['parents'] = [origin_id_to_id(x) for x in parents if x not in self.skip_orgs]

        self.save_organization(org)

    def _import_children(self, org):
        if not 'children' in org:
            return
        for ch in org['children']:
            self._import_organization(ch)
        for ch in org['children']:
            self._import_children(ch)

    def import_organizations(self):
        data_path = os.path.join(settings.PROJECT_ROOT, 'data')
        org_file = open(os.path.join(data_path, 'organizations.json'), 'r')
        org_list = json.load(org_file)

        queryset = Organization.objects.all()
        self.skip_orgs = set()
        self.org_syncher = ModelSyncher(queryset, lambda obj: obj.id, delete_func=mark_deleted)

        self.org_dict = {org['id']: org for org in org_list}
        ordered = []
        # Start import from the root orgs, move down level by level.
        while len(ordered) != len(org_list):
            for org in org_list:
                if 'added' in org:
                    continue
                if not org['parents']:
                    org['added'] = True
                    ordered.append(org)
                    continue
                for p in org['parents']:
                    if not 'added' in self.org_dict[p]:
                        break
                else:
                    org['added'] = True
                    ordered.append(org)

        for org in ordered:
            self._import_organization(org)
