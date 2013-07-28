from haystack import indexes
from ahjodoc.models import *

class IssueIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_updated_field(self):
        return 'last_modified_time'

    def get_model(self):
        return Issue

class AgendaItemIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_updated_field(self):
        return 'last_modified_time'

    def get_model(self):
        return AgendaItem
