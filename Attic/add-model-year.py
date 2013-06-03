from ahjodoc.models import *

doc_list = MeetingDocument.objects.all()

for doc in doc_list:
    if not '2013' in doc.origin_id:
        old = doc.origin_id
        arr = doc.origin_id.split('_')
        arr[2] = '2013-' + arr[2]
        doc.origin_id = '_'.join(arr)
        print "%s -> %s" % (old, doc.origin_id)
        doc.save()
    else:
        print "no: %s" % doc.origin_id
