import os
import re
import logging
import itertools
import datetime
from collections import defaultdict

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.gdal import SpatialReference, CoordTransform

from modeltranslation.translator import translator

from .util import active_language
from decisions.models import Organization, Person


# Using a recursive default dictionary
# allows easy updating of the same data keys
# with different languages on different passes.
def recur_dict(): return defaultdict(recur_dict)

class Importer(object):
    def __init__(self, options):
        super(Importer, self).__init__()
        self.options = options
        self.verbosity = options['verbosity']
        self.logger = logging.getLogger(__name__)

        self.setup()

    def setup(self):
        pass

    @staticmethod
    def clean_text(text):
        text = text.replace('\n', ' ')
        # remove consecutive whitespaces
        return re.sub(r'\s\s+', ' ', text, re.U).strip()

    def _set_field(self, obj, field_name, val):
        if not hasattr(obj, field_name):
            print(vars(obj))
        obj_val = getattr(obj, field_name)
        if obj_val == val:
            return
        setattr(obj, field_name, val)
        obj._changed_fields.append(field_name)

    def _update_fields(self, obj, info, skip_fields):
        obj_fields = list(obj._meta.fields)
        trans_fields = translator.get_options_for_model(type(obj)).fields
        for field_name, lang_fields in trans_fields.items():
            lang_fields = list(lang_fields)
            for lf in lang_fields:
                lang = lf.language
                # Do not process this field later
                skip_fields.append(lf.name)

                if field_name not in info:
                    continue

                data = info[field_name]
                if data is not None and lang in data:
                    val = data[lang]
                else:
                    val = None
                self._set_field(obj, lf.name, val)

            # Remove original translated field
            skip_fields.append(field_name)

        for d in skip_fields:
            for f in obj_fields:
                if f.name == d:
                    obj_fields.remove(f)
                    break

        if 'origin_id' in info:
            info['origin_id'] = str(info['origin_id'])

        for field in obj_fields:
            field_name = field.name
            if field_name not in info:
                continue
            self._set_field(obj, field_name, info[field_name])

    def save_organization(self, info):
        obj = self.org_syncher.get(info['id'])
        if not obj:
            obj = Organization(id=info['id'])
            obj._created = True
        else:
            obj._created = False

        obj._changed_fields = []

        skip_fields = ['id', 'contact_details', 'parents']
        self._update_fields(obj, info, skip_fields)

        if obj._created or obj._changed_fields:
            obj.save()

        if obj._changed_fields or obj._created:
            if obj._created:
                verb = "created"
            else:
                verb = "changed"
            print("%s %s (%s)" % (obj, verb, ', '.join(obj._changed_fields)))

        self.org_syncher.mark(obj)

        return

importers = {}

def register_importer(klass):
    importers[klass.name] = klass
    return klass


def get_importers():
    if importers:
        return importers
    # Importing the packages will cause their register_importer() methods
    # being called.
    for fname in os.listdir(os.path.dirname(__file__)):
        module, ext = os.path.splitext(fname)
        if ext.lower() != '.py':
            continue
        if module in ('__init__', 'base'):
            continue
        full_path = "%s.%s" % (__package__, module)
        ret = __import__(full_path, locals(), globals())
    return importers
