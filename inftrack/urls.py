"""inftrack URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import login,logout
from django.urls import path, re_path
from django.conf.urls import url

import inftrackapp.views as views

from django.conf.urls import url
from rest_framework_swagger.views import get_swagger_view

schema_view = get_swagger_view(title='Swagger API')

# urlpatterns = [
    
# ]

urlpatterns = [
    url(r'^$', schema_view),
        
    re_path(r'v1/people', views.show_all_people),

    re_path(r'v1/people?role=(?P<role>[A-Z,a-z]{1,12})', views.show_people_by_role),

    re_path(r'v1/people?status=(?P<status>[A-Z,a-z]{1,12})', views.show_people_by_status),

    re_path(r'v1/status?id=(?P<id>.{1,50})', views.show_person_by_id),

    re_path(r'v1/status?id=(?P<id>.{1,50})&status=(?P<status>[A-Z]{1,12})', views.update_status)
]
