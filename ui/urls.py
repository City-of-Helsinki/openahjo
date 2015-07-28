from django.conf.urls import patterns
from django.views.generic.base import RedirectView
from django.conf import settings

prefix = getattr(settings, 'URL_PREFIX', '')

urlpatterns = patterns('',
    (r'^$', 'ui.views.home_view'),
    (r'^asia/$', 'ui.views.issue_list'),
    (r'^asia/kartta/$', 'ui.views.issue_list_map'),
    (r'^asia/(?P<slug>[\w-]+)/(?P<pm_slug>[\w-]+)-(?P<year>\d+)-(?P<number>\d+)/((?P<index>\d+)/)?$', 'ui.views.issue_details'),
    (r'^asia/(?P<slug>[\w-]+)/$', 'ui.views.issue_details'),
    (r'^paattaja/$', 'ui.views.policymaker_list'),
    (r'^paattaja/(?P<slug>[\w-]+)/((?P<year>\d+)/(?P<number>\d+)/)?$', 'ui.views.policymaker_details'),
    (r'^tietoa/$', 'ui.views.about'),

    (r'^issue(?P<rest>.*)$', RedirectView.as_view(url='/' + prefix + 'asia%(rest)s')),
    (r'^policymaker(?P<rest>.*)$', RedirectView.as_view(url='/' + prefix + 'paattaja%(rest)s')),
    (r'^about(?P<rest>.*)$', RedirectView.as_view(url='/' + prefix + 'tietoa%(rest)s')),
)
