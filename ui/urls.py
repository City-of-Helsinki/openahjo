from django.conf.urls import patterns

urlpatterns = patterns('',
    (r'^$', 'ui.views.home_view'),
    (r'^issue/(?P<slug>[\w-]+)/$', 'ui.views.issue_view'),
)
