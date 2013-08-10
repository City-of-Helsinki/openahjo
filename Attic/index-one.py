from haystack import connections as haystack_connections
from haystack.query import SearchQuerySet
from ahjodoc.models import *

model = Issue
filters = {'slug': 'hel-2013-000694'}
#filters = {'id': 1}

backends = haystack_connections.connections_info.keys()
for backend_name in backends:
    unified_index = haystack_connections[backend_name].get_unified_index()
    print unified_index
    index = unified_index.get_index(model)
    print index
    backend = haystack_connections[backend_name].get_backend()
    print backend
    qs = Issue.objects.filter(**filters)
    for obj in qs:
        txt = index.full_prepare(obj)['text']
        lines = txt.split('\n')
        #print txt
        #for l in lines:
            #if 'palautusehdotus' in l.lower():
                #print l
    backend.update(index, qs)
