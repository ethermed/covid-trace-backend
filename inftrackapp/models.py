##############################################################################################################
# models.py
# This is where we specify all the data models we use
##############################################################################################################
from __future__ import unicode_literals

import sys
import datetime
import time
import json
import itertools
import logging
import os
import os.path
import re
import base64
from uuid import uuid4

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError, FieldDoesNotExist
import django.core.validators as validators
from django.db import models, IntegrityError

import logging
logger = logging.getLogger(__name__)

ROLE_DOCTOR = "doctor"
ROLE_NURSE = "nurse"
ROLE_STAFF = "staff"
ROLE_PATIENT = "patient"
ROLE_OTHER = "other"
ROLE_CHOICES = (
    (ROLE_DOCTOR, "Doctor"),
    (ROLE_NURSE, "Nurse"),
    (ROLE_STAFF, "Staff"),
    (ROLE_PATIENT, "Patient"),
    (ROLE_OTHER, "Other")
)

ASSIGN_EVENT_ASSIGNED = "assigned"
ASSIGN_EVENT_UNASSIGNED = "unassigned"
ASSIGN_EVENT_CHOICES = (
    (ASSIGN_EVENT_ASSIGNED, "Assigned"),
    (ASSIGN_EVENT_UNASSIGNED, "Unassigned")
)

STATUS_OK = "ok"
STATUS_AT_RISK = "at_risk"
STATUS_BEING_TESTED = "being_tested"
STATUS_INFECTED = "infected"
STATUS_CHOICES = (
    (STATUS_OK, "Ok"),
    (STATUS_AT_RISK, "At Risk"),
    (STATUS_BEING_TESTED, "Being Tested"),
    (STATUS_INFECTED, "Infected")
)
STATUS_CHECK = [STATUS_OK, STATUS_AT_RISK, STATUS_BEING_TESTED, STATUS_INFECTED]

################################################
# Managers and QuerySet overrides
# These give us convenience method get_or_none
################################################
class EthermedQuerySet(models.query.QuerySet):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except ObjectDoesNotExist:
            return None

#
# EthermedQueryManager: just adds in method get_or_none to return None for object when it doesn't exist
#
class EthermedQueryManager(models.Manager.from_queryset(EthermedQuerySet)):
    pass

#
###############################
# EthermedModel: base class
# for all models except for
# the actual data points
###############################
class EthermedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    @classmethod
    def newInstance(cls,*args,**kwargs):
        return cls(*args,**kwargs)

    def _descr_string(self,modelName,vars):
        kwdict={}
        s="%s [id=%s" % (modelName,getattr(self,"id","undefined"))
        for v in vars:
            s+=", %s={%s}" % (v,v)
            kwdict[v] = getattr(self,v,"undefined")
        s+="]"
        s=s.format(**kwdict)
        return s

    class Meta:
        abstract = True

##########################################
# TrackablePerson
##########################################
class TrackablePerson(EthermedModel):
    #
    # override manager so we get custom behavior get_or_none
    #
    objects = EthermedQueryManager()

    unique_id = models.CharField(max_length=50,unique=True,null=False,blank=False)

    firstname = models.CharField(max_length=50,null=False,blank=False)
    lastname = models.CharField(max_length=50,null=False,blank=False)
    phone = models.CharField(max_length=50,null=False,blank=False)
    email = models.CharField(max_length=100,null=True,blank=True)
    role = models.CharField(max_length=12,null=False,blank=False,choices=ROLE_CHOICES)
    status = models.CharField(max_length=12,null=False,blank=False,choices=STATUS_CHOICES)

    ####################################
    # custom methods
    ####################################
    #
    @property
    def current_tag(self):
        try:
            tag_assign_event = TagAssignmentEvent.objects.filter(person=self).order_by('-timestamp')[0]
        except Exception as ex:
            return None
        if tag_assign_event.event_type ==  ASSIGN_EVENT_ASSIGNED:
            return tag_assign_event.tag
        else:
            return None

    def __str__(self):
        modelName="TrackablePerson"
        vars=["unique_id", "firstname","lastname","phone","email","role","status"]
        return self._descr_string(modelName,vars)

    class Meta:
        db_table = 'ethermed_trackable_person'

##########################################
# TrackingTag
##########################################
class TrackingTag(EthermedModel):
    #
    # override manager so we get custom behavior get_or_none
    #
    objects = EthermedQueryManager()

    unique_id = models.CharField(max_length=50,unique=True,null=False,blank=False)

    ####################################
    # custom methods
    ####################################
    #
    @property
    def current_person(self):
        try:
            tag_assign_event = TagAssignmentEvent.objects.filter(tag=self).order_by('-timestamp')[0]
        except Exception as ex:
            return None
        if tag_assign_event.event_type ==  ASSIGN_EVENT_ASSIGNED:
            return tag_assign_event.person
        else:
            return None

    def __str__(self):
        modelName="TrackingTag"
        vars=["unique_id"]
        return self._descr_string(modelName,vars)

    class Meta:
        db_table = 'ethermed_tracking_tag'

##########################################
# TagAssignmentEvent
##########################################
class TagAssignmentEvent(EthermedModel):
    #
    # override manager so we get custom behavior get_or_none
    #
    objects = EthermedQueryManager()

    person = models.ForeignKey('TrackablePerson',null=False,on_delete=models.CASCADE,related_name='tag_assignment_events')
    tag = models.ForeignKey('TrackingTag',null=False,on_delete=models.CASCADE,related_name='tag_assignment_events')
    event_type =  models.CharField(max_length=16,null=False,blank=False,choices=ASSIGN_EVENT_CHOICES)
    timestamp = models.DateTimeField()

    ####################################
    # custom methods
    ####################################
    #

    def __str__(self):
        modelName="TagAssignmentEvent"
        vars=["person","tag","event_type","timestamp"]
        return self._descr_string(modelName,vars)

    class Meta:
        db_table = 'ethermed_tag_assignment_event'

##########################################
# StatusChangeEvent
##########################################
class StatusChangeEvent(EthermedModel):
    #
    # override manager so we get custom behavior get_or_none
    #
    objects = EthermedQueryManager()

    #
    # we don't yet have user login so we won't have users but eventually we will need this
    #
    # user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='status_change_events')

    person = models.ForeignKey('TrackablePerson',null=False,on_delete=models.CASCADE,related_name='status_change_events')
    prior_status = models.CharField(max_length=12,null=False,blank=False,choices=STATUS_CHOICES)
    new_status = models.CharField(max_length=12,null=False,blank=False,choices=STATUS_CHOICES)
    timestamp = models.DateTimeField()

    ####################################
    # custom methods
    ####################################
    # None

    def __str__(self):
        modelName="TagAssignmentEvent"
        vars=["person","prior_status","new_status","timestamp"]
        return self._descr_string(modelName,vars)

    class Meta:
        db_table = 'ethermed_status_change_event'

##########################################
# TagPosition
# There will be many records of these
##########################################
class TagPosition(models.Model):
    tag = models.ForeignKey('TrackingTag',null=False,on_delete=models.CASCADE,related_name='positions')
    person = models.ForeignKey('TrackablePerson',null=False,on_delete=models.CASCADE,related_name='positions')
    x = models.FloatField(null=False,blank=False,default=0.0)
    y = models.FloatField(null=False,blank=False,default=0.0)
    timestamp = models.DateTimeField()

    def __str__(self):
        modelName="TagPosition"
        vars=["tag","person","x","y","timestamp"]
        return self._descr_string(modelName,vars)

    class Meta:
        db_table = 'ethermed_tag_position'
