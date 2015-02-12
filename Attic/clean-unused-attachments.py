import os
from ahjodoc.models import Attachment

att_list = set(list(Attachment.objects.values_list('hash', flat=True)))
root_path = 'media/att'
l1_dir = os.listdir(root_path)
to_remove = set()
for l1d in l1_dir:
    files = os.listdir(os.path.join(root_path, l1d))
    for fn in files:
        h = fn.split('.')[0]
        if h not in att_list:
            to_remove.add(os.path.join(root_path, l1d, fn))

if len(to_remove) * 1.0 / len(att_list) > 0.1:
    raise Exception("Too many attachments (%d) to be removed!" % len(to_remove))

for fn in to_remove:
    os.unlink(fn)

if len(to_remove):
    print("%d unused attachments removed" % len(to_remove))
