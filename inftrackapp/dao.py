#######################################################################
# dao.py
# Database helper functions
#######################################################################
import datetime
from django.utils.timezone import make_aware
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
import inftrackapp.models as models

def add_secs_to_datetime(dtobj,secs=1):
    return dtobj + datetime.timedelta(seconds=secs)

def get_all_people():
    people = models.TrackablePerson.objects.all()
    return people

def get_all_people_with_role(role):
    people = models.TrackablePerson.objects.filter(role=role)
    return people

def get_all_people_with_status(status):
    people = models.TrackablePerson.objects.filter(status=status)
    return people

def get_all_people_with_role_and_status(role,status):
    people = models.TrackablePerson.objects.filter(role=role,status=status)
    return people

def add_person(firstname=None,lastname=None,unique_id=None,phone=None,email=None,role=None,status=None):
    person = models.TrackablePerson()
    person.unique_id = unique_id   
    person.firstname = firstname
    person.lastname = lastname
    person.phone = phone 
    person.email = email
    person.role = role
    person.status=status
    person.save()
    return person

def get_person(unique_id):
    return models.TrackablePerson.objects.get_or_none(unique_id=unique_id)

def add_tag(unique_id=None):
    tag = models.TrackingTag()
    tag.unique_id = unique_id
    tag.save()
    return tag

def unassign_tag(tag,dt):
    current_person = tag.current_person
    if current_person:
        evt = models.TagAssignmentEvent()
        evt.tag=tag
        evt.person=current_person
        evt.event_type=models.ASSIGN_EVENT_UNASSIGNED
        evt.timestamp = make_aware(dt)
        evt.save() 

def assign_tag(tag,person,dt):
    #
    # is this tag assigned to anyone right now?
    #
    current_person = tag.current_person
    if current_person:
        # make sure this dt is before assignment dt?
        unassign_tag(tag,current_person,dt)
    evt = models.TagAssignmentEvent()
    evt.tag=tag
    evt.person=person
    evt.event_type=models.ASSIGN_EVENT_ASSIGNED

    newdt = add_secs_to_datetime(dt,secs=1)

    evt.timestamp = make_aware(newdt)
    evt.save() 

def change_person_status(person,status,dt):
    prior_status=person.status
    person.status=status
    person.save()

    evt=models.StatusChangeEvent()
    evt.person=person
    evt.prior_status=prior_status
    evt.status=person.status
    evt.timestamp=make_aware(dt)
    evt.save()

def make_position(tag,person,x,y,timestamp):
    tagpos = models.TagPosition(tag=tag,person=person,x=x,y=y,timestamp=make_aware(timestamp))
    return tagpos

def save_position(tag,person,x,y,timestamp):
    tagpos = models.TagPosition(tag=tag,person=person,x=x,y=y,timestamp=make_aware(timestamp))
    return tagpos

def save_positions(tagpos_list):
    models.TagPosition.objects.bulk_create(tagpos_list)

def get_person_position_trace(person,fromdt,todt):
    return models.TagPosition.objects.filter(timestamp__gte=fromdt, timestamp__lte=todt)

