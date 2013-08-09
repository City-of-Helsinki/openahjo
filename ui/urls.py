from django.conf.urls import patterns

urlpatterns = patterns('',
    (r'^$', 'ui.views.home_view'),
    (r'^issue/$', 'ui.views.issue_list'),
    (r'^issue/map/$', 'ui.views.issue_list_map'),
    (r'^issue/(?P<slug>[\w-]+)/$', 'ui.views.issue_details'),
    (r'^policymaker/$', 'ui.views.policymaker_list'),
    (r'^policymaker/(?P<slug>[\w-]+)/((?P<year>\d+)/(?P<number>\d+)/)?$', 'ui.views.policymaker_details'),
)
