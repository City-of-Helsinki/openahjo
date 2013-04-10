from django.conf.urls import patterns

urlpatterns = patterns('',
    (r'^$', 'demo.views.demo_view')
)
