from django.shortcuts import render_to_response
from django.conf import settings

def home_view(request):
    prefix = getattr(settings, 'URL_PREFIX', '')
    return render_to_response('home.html', {'API_PREFIX': '/' + prefix})
