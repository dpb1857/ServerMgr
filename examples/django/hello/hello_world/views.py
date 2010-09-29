# Create your views here.

from django.http import HttpResponse

def HelloWorld(request):
    """Display "hello, world" message."""

    return HttpResponse("Hello, world.")
