from django.shortcuts import render_to_response

def demo_view(request):
    return render_to_response('demo.html')
