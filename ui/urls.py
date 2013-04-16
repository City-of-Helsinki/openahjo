from django.conf.urls import patterns

urlpatterns = patterns('',
    (r'^$', 'ui.views.home_view'),
    (r'^item/(?P<slug>[\w-]+)/$', 'ui.views.item_view'),
)
