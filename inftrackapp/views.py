from django.shortcuts import render

# Create your views here.
import datetime
import json
import os
import logging
import random

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
def show_people_by_role(request, role):
    #comma delimited roles or one role
    role_value = role

    #handling one role
    if ',' not in role_value:
        if role_value not in models.ROLE_CHECK:
            return api_json.response_error_not_found("the value is not a valid role")
        trackable_people = models.TrackablePerson.objects.filter(role=role_value)
    else:
        #handling multiple roles
        roles = role_value.split(",")
        trackable_people = models.TrackablePerson.objects.filter(role__in=roles)

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
def show_people_by_status(request, status):
    #comma delimited statuses or one statuses
    status_value = status

    #handling one status
    if ',' not in status_value:
        if status_value not in models.STATUS_CHECK:
            return api_json.response_error_not_found("the value is not a valid status")
        trackable_people = models.TrackablePerson.objects.filter(status=status_value)
    else:
        #handling multiple statuses
        statuses = status_value.split(",")
        trackable_people = models.TrackablePerson.objects.filter(status__in=statuses)

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
def show_person_by_id(request, identifier):
    try:
        trackable_people = models.TrackablePerson.objects.filter(unique_id=identifier)
        person = trackable_people[0]

        person_dict = {
            "firstname": person.firstname,
            "lastname": person.lastname,
            "id": person.unique_id,
            "role": person.role,
            "status": person.status,
            "phone": person.phone,
            "email": person.email
        }
        return api_json.response_success_with_dict(person_dict)
    except:
        return api_json.response_error_not_found("no person with specified id")

# v1/status?id=123&status=ok
def update_status(request, status, identifier):
    #get the user with id
    updated_persons = models.TrackablePerson.objects.filter(unique_id=identifier)
    updated_person = updated_persons[0]

    if updated_person is None:
        return api_json.response_error_not_found("no person with specified id in our system")

    #fetching new status value
    status_update = status

    #checking to see if the new status value is a valid status
    if status_update in models.STATUS_CHECK:
        setattr(updated_person,"status",status_update)
        updated_person.save()
        response_dict = {
            "firstname": updated_person.firstname,
            "lastname": updated_person.lastname,
            "id": updated_person.unique_id,
            "role": updated_person.role,
            "status": updated_person.status,
            "phone": updated_person.phone,
            "email": updated_person.email }
        return api_json.response_success_with_dict(response_dict)
    else:
        return api_json.response_error_not_found("status value is not a valid status")


def analyze_at_risk(request, identifier):
    trackable_people = models.TrackablePerson.objects.all()
    increment = random.randrange(10)+1 #random value from 1-10

    people_list = []
    count = 0
    index = 0
    for person in trackable_people:
        risk = round(random.random(), 2) #random float with 2 decimal places from 0.0 to 1.0
        if count < 10 and person.unique_id != identifier and index % increment == 0:
            person_dict = {
                "firstname": person.firstname,
                "lastname": person.lastname,
                "id": person.unique_id,
                "risk": risk,
                "status": person.status
            }
            people_list.append(person_dict)
            count += 1
        index += 1

    return api_json.response_success_with_list(people_list)

def analyze_at_risk_details(request):
    amount = random.randrange(10)+1 #how many results
    zone = "break room"

    result_list = []
    for i in range(amount):
        month = random.randrange(3,12)
        day = random.randrange(1,29)
        hour = random.randrange(0,23)
        min = random.randrange(0,59)

        starttime = "2020-"+month+"-"+day+" "+hour+":"+min+":00.000000"

        increment = random.randrange(1,15)

        if min + increment >= 60:
            min = min + increment - 60
            hour += 1
        else:
            min = min + increment

        endtime = "2020-"+month+"-"+day+" "+hour+":"+min+":00.000000"

        result_dict = {
            "starttime": starttime,
            "endtime": endtime,
            "zone": zone
        }
        result_list.append(result_dict)

    return api_json.response_success_with_list(result_list)
