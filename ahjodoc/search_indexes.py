from haystack import indexes
from ahjodoc.models import *

class MultiValueIntegerField(indexes.MultiValueField):
    field_type = 'integer'
    def __init__(self, **kwargs):
        if kwargs.get('facet_class') is None:
            kwargs['facet_class'] = FacetMultiValueIntegerField
        super(MultiValueIntegerField, self).__init__(**kwargs)

class FacetMultiValueIntegerField(indexes.FacetField, MultiValueIntegerField):
    pass

class IssueIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    category = indexes.IntegerField(faceted=True)
    categories = MultiValueIntegerField(faceted=True)
    districts = indexes.MultiValueField(faceted=True)

    def get_updated_field(self):
        return 'last_modified_time'

    def prepare_category(self, obj):
        return obj.category.pk
    def prepare_categories(self, obj):
        cat_tree = obj.category.get_ancestors(include_self=True)
        return [x.pk for x in cat_tree]

    def prepare_districts(self, obj):
        districts = obj.districts.all()
        return [x.name for x in districts]

    def get_model(self):
        return Issue

class AgendaItemIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_updated_field(self):
        return 'last_modified_time'

    def get_model(self):
        return AgendaItem
