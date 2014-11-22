#!/usr/bin/env python

import os
from django.conf import settings
from ahjodoc.models import *

att_dict = {att.file: att for att in Attachment.objects.all()}

count = 0

for root, dirs, files in os.walk(settings.MEDIA_ROOT + 'att'):
    for fname in files:
        dir_name = os.path.split(root)[-1]
        fpath = 'att/' + dir_name + '/' + fname
        prin
        if not fpath in att_dict:
            print fpath
    count += 1

print count
