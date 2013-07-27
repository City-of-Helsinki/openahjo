from django.conf.urls import patterns

urlpatterns = patterns('',
    (r'^$', 'ui.views.home_view'),
    (r'^meeting/$', 'ui.views.meeting_list'),
    (r'^meeting/(?P<slug>[\w-]+)/$', 'ui.views.meeting_details'),
    (r'^issue/$', 'ui.views.issue_list'),
    (r'^issue/(?P<slug>[\w-]+)/$', 'ui.views.issue_details'),
    (r'^policymaker/$', 'ui.views.policymaker_list'),
    (r'^policymaker/(?P<slug>[\w-]+)/$', 'ui.views.policymaker_details'),
    (r'^policymaker/(?P<slug>[\w-]+)/(?P<year>\d+)/(?P<number>\d+)/$', 'ui.views.policymaker_details'),
)
