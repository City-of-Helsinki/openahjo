from django.conf.urls import patterns

urlpatterns = patterns('',
    (r'^$', 'ui.views.home_view')
)
