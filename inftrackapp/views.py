from django.shortcuts import render

# Create your views here.
import datetime
import json
import os
import logging

from operator import or_

from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q

from django.core.exceptions import ObjectDoesNotExist
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

import inftrackapp.models as models
import inftrackapp.api_json as api_json

# v1/people
def show_all_people(request):
    trackable_people = models.TrackablePerson.objects.all()
    people_list = []
    for person in trackable_people:
        person_dict = {
            "firstname": person.firstname,
            "lastname": person.lastname,
            "id": person.unique_id,
            "role": person.role,
            "status": person.status,
            "phone": person.phone,
            "email": person.email
        }
        people_list.append(person_dict)
    return api_json.response_success_with_list(people_list)

# v1/people?role=doctor
# v1/people?role=doctor,nurse,patient
def show_people_by_role(request,*args,**kwargs):
    #comma delimited roles or one role
    role_value = kwargs["role"]
    #handling one role
    if ',' not in role_value:
        trackable_people = models.TrackablePerson.objects.filter(role=role_value)
    else:
        #handling multiple roles
        roles = role_value.split(",")
        trackable_people = models.TrackablePerson.objects.filter(reduce(or_, [Q(role__icontains=role) for role in roles]))

    people_list = []
    for person in trackable_people:
        person_dict = {
            "firstname": person.firstname,
            "lastname": person.lastname,
            "id": person.unique_id,
            "role": person.role,
            "status": person.status,
            "phone": person.phone,
            "email": person.email
        }
        people_list.append(person_dict)
    return api_json.response_success_with_list(people_list)

# v1/people/?status=ok
# v1/people/?status=at-risk,being-tested
def show_people_by_status(request,*args,**kwargs):
    #comma delimited statuses or one statuses
    status_value = kwargs["status"]
    #handling one status
    if ',' not in status_value:
        trackable_people = models.TrackablePerson.objects.filter(status=status_value)
    else:
        #handling multiple statuses
        statuses = status_value.split(",")
        trackable_people = models.TrackablePerson.objects.filter(reduce(or_, [Q(status__icontains=status) for status in statuses]))

    people_list = []
    for person in trackable_people:
        person_dict = {
            "firstname": person.firstname,
            "lastname": person.lastname,
            "id": person.unique_id,
            "role": person.role,
            "status": person.status,
            "phone": person.phone,
            "email": person.email
        }
        people_list.append(person_dict)
    return api_json.response_success_with_list(people_list)
