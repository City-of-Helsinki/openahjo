from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from tastypie.api import Api
from ahjodoc.api import all_resources
from munigeo.api import DistrictResource

v1_api = Api(api_name='v1')
for res in all_resources:
    v1_api.register(res())
v1_api.register(DistrictResource())

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'openahjo.views.home', name='home'),
    # url(r'^openahjo/', include('openahjo.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^', include(v1_api.urls)),
    url(r'^', include('ui.urls')),
    url(r'^doc/', include('tastypie_swagger.urls', namespace='tastypie_swagger')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
