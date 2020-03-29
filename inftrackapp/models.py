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

    #
    # This returns a dictionary of other people and my interactions with them
    #
    def get_my_interactions(self,startdate,enddate,reverse_order=False):
        #
        # a TagPosition object tagpos.interaction_event_tag_positions gives a list of InteractionEventTagPosition objects for this person
        # each of these objects has a reference to InteractionEvent
        # The other person in the interaction event is interaction_event.other_person(person)
        #

        #
        # this gives a list of tag_positions where each object has obj.interaction_event_tag_positions filled out
        #
        if reverse_order:
            orderbystr = '-timestamp'
        else:
            orderbystr = 'timestamp'
        #
        # get a list of my InteractionEvent objects in the specified timeframe
        #
        my_events = [obj.interaction_event for obj in InteractionEventTagPosition.objects.\
                    select_related('interaction_event').\
                    select_related('tag_position__person').\
                    filter(tag_position__person=self, timestamp__gte=startdate, timestamp__lte=enddate).\
                    order_by(orderbystr)]

        response_dict={}
        for evt in my_events:
            other_person=evt.other_person
            if other_person.unique_id not in response_dict:
                response_dict[other_person.unique_id] = {
                    "other_person": {
                        "unique_id": other_person.unique_id,
                        "name": other_person.firstname + " " + other_person.lastname
                    },
                    "interactions": []
                }
            #
            # now the other person is in the output so add the interaction event info to list of interaction events
            #
            evtinfo = {
                "interaction_event_id": evt.id, 
                "distance": evt.distance, 
                "timestamp": evt.timestamp, 
                "prior_interaction_event_id": evt.prior_interaction_event.id, 
                "next_interaction_event_id": evt.next_interaction_event.id
            }
            response_dict[other_person.unique_id]["interactions"].append(evtinfo)

        return response_dict

    #
    # This returns a dictionary of other people and my interactions with them
    #
    def get_my_interactions_with(self,specific_other_person,startdate,enddate,reverse_order=False):
        #
        # this gives a list of tag_positions where each object has obj.interaction_event_tag_positions filled out
        #
        if reverse_order:
            orderbystr = '-timestamp'
        else:
            orderbystr = 'timestamp'
        #
        # get a list of my InteractionEvent objects in the specified timeframe
        #
        my_events = [obj.interaction_event for obj in InteractionEventTagPosition.objects.\
                    select_related('interaction_event').\
                    select_related('tag_position__person').\
                    filter(tag_position__person=self, timestamp__gte=startdate, timestamp__lte=enddate).\
                    order_by(orderbystr)]


        response_dict={}
        for evt in my_events:
            other_person=evt.other_person
            if other_person==specific_other_person:
                if other_person.unique_id not in response_dict:
                    response_dict[other_person.unique_id] = {
                        "other_person": {
                            "unique_id": other_person.unique_id,
                            "name": other_person.firstname + " " + other_person.lastname
                        },
                        "interactions": []
                    }
            #
            # now the other person is in the output so add the interaction event info to list of interaction events
            #
            evtinfo = {
                "interaction_event_id": evt.id, 
                "distance": evt.distance, 
                "timestamp": evt.timestamp, 
                "prior_interaction_event_id": evt.prior_interaction_event.id, 
                "next_interaction_event_id": evt.next_interaction_event.id
            }
            response_dict[other_person.unique_id]["interactions"].append(evtinfo)

        return response_dict

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


##########################################
# InteractionEventTagPosition
# There will be many records of these
##########################################
class InteractionEventTagPosition(models.Model):
    interaction_event = models.ForeignKey('InteractionEvent',null=False,on_delete=models.CASCADE,related_name='interaction_event_tag_positions')
    tag_position = models.ForeignKey('TagPosition',null=False,on_delete=models.CASCADE,related_name='interaction_event_tag_positions')

    def __str__(self):
        modelName="InteractionEventPerson"
        vars=["interaction_event","tag_position"]
        return self._descr_string(modelName,vars)

    class Meta:
        db_table = 'ethermed_interaction_event_tag_position'

##########################################
# InteractionEvent
# There will be many records of these
##########################################
class InteractionEvent(models.Model):
    distance = models.FloatField(null=False,blank=False,default=0.0)
    timestamp = models.DateTimeField()
    prior_interaction_event = models.OneToOneField('self', null=True, blank=True, on_delete=models.SET_NULL,related_name="next_interaction_event")

    @property
    def persons(self):
        return [tag_position.person for tag_position in self.interaction_event_tag_positions.all()]

    @property
    def tags(self):
        return [tag_position.tag for tag_position in self.interaction_event_tag_positions.all()]

    @property
    def other_person(self, person):
        for p in self.persons:
            if p.unique_id != person.unique_id:
                return p

    @property
    def other_tag(self, tag):
        for t in self.tags:
            if t.unique_id != t.unique_id:
                return t

    def __str__(self):
        modelName="InteractionEvent"
        vars=["distance","timestamp","prior_interaction_event_id"]
        return self._descr_string(modelName,vars)

    class Meta:
        db_table = 'ethermed_interaction_event'


