from django.conf.urls.defaults import *


import hello_world.views as views

urlpatterns = patterns('',
                       (r'^.*$', views.HelloWorld)
                       )
