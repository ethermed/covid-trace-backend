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
def show_people_by_role(self, request, *args, **kwargs):
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

# v1/people?status=ok
# v1/people?status=at-risk,being-tested
def show_people_by_status(self, request, *args, **kwargs):
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

# v1/status?id=123
def show_person_by_id(self, request, *args, **kwargs):
    id = kwargs["id"]
    trackable_people = models.TrackablePerson.objects.filter(unique_id=id)
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

# v1/status?id=123&status=ok
def update_status(self, request, *args, **kwargs):
    #get the user with id
    updated_persons = models.TrackablePerson.objects.filter(unique_id=kwargs["id"])
    updated_person = updated_persons[0]

    #fetching new status value
    status_update = kwargs["status"]

    #checking to see if the new status value is a valid status
    if status_update in STATUS_CHOICES:
        setattr(updated_person,"status",status_update)

    updated_person.save()

    response_dict = {
        "firstname": updated_person.firstname,
        "lastname": updated_person.lastname,
        "id": updated_person.unique_id,
        "role": updated_person.role,
        "status": updated_person.status,
        "phone": updated_person.phone,
        "email": updated_person.email
    }
    return api_json.response_success_with_dict(response_dict)
