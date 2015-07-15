import os
from django.conf import settings
from ahjodoc.models import *
from optparse import make_option
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Prune deleted attachments"

    def delete_attachment(self, fpath):
        print(fpath)

    def handle(self, **options):
        att_dict = {att.file: att for att in Attachment.objects.all()}
        total_count = len(att_dict)

        root_path = os.path.join(settings.MEDIA_ROOT, 'att')
        to_delete = []

        for root, dirs, files in os.walk(root_path):
            for fname in files:
                dir_name = os.path.split(root)[-1]
                fpath = 'att/' + dir_name + '/' + fname
                if fpath not in att_dict:
                    to_delete.append(fpath)

        if float(len(to_delete)) / total_count > 0.1:
            raise Exception('Attempting to delete too many attachments')

        for fpath in to_delete:
            full_path = os.path.join(settings.MEDIA_ROOT, fpath)
            print(full_path)
            os.remove(full_path)
