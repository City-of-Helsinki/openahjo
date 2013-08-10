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
    location = indexes.LocationField()
    policymakers = MultiValueIntegerField(faceted=True)

    def get_updated_field(self):
        return 'last_modified_time'

    def prepare_category(self, obj):
        return obj.category.pk
    def prepare_categories(self, obj):
        cat_tree = obj.category.get_ancestors(include_self=True)
        return [x.pk for x in cat_tree]

    def prepare_policymakers(self, obj):
        ai_list = obj.agendaitem_set.all()
        pm_list = set([ai.meeting.policymaker.id for ai in ai_list])
        return list(pm_list)

    def prepare_districts(self, obj):
        districts = obj.districts.all()
        return [x.name for x in districts]

    def prepare_location(self, obj):
        for g in obj.geometries.all():
            if g.geometry.geom_type == 'Point':
                return "%f,%f" % (g.geometry.y, g.geometry.x)
        return None

    def prepare_text(self, obj):
        field = self.fields['text']
        ret = field.prepare(obj)
        lines = ret.split('\n')
        # remove duplicate lines
        seen = set()
        result = []
        dupes = False
        for line in lines:
            if line not in seen:
                result.append(line)
                seen.add(line)
        ret = '\n'.join(result)
        return ret

    def get_model(self):
        return Issue

class AgendaItemIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_updated_field(self):
        return 'last_modified_time'

    def get_model(self):
        return AgendaItem
