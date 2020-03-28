import json

from uuid import UUID

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden

KEY_CODE ='code'
KEY_MESSAGE = 'msg'
VALUE_SUCCESS = 'success'
VALUE_ERROR = 'error'
KEY_RESULT = 'result'

###########################
# utility function
###########################
def fallback_decoder(obj):
    if type(obj) is UUID:
        return str(obj)
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError('Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj)))

###########################
# success handlers
###########################
def response_json(dict_in):
    return HttpResponse(json.dumps(dict_in, default=fallback_decoder), content_type='application/json')

def response_success_with_dict(dict_in):
    return HttpResponse(json.dumps(dict_in, default=fallback_decoder), content_type='application/json')

def response_success_with_list(list_in,limit=0,offset=0,total=0):
    cnt=len(list_in)
    thedict={
        "count": cnt,
        "has_more": False,
        "limit": limit,
        "offset": offset,
        "total": total,
        "results": list_in
    }
    return HttpResponse(json.dumps(thedict, default=fallback_decoder), content_type='application/json')

class HttpResponseDeleteSuccessful(HttpResponse):
    status_code = 204

def response_delete_successful():
    return HttpResponseDeleteSuccessful()

###########################
# error handlers
###########################
#
# HttpResponse custom classes
#
class HttpResponseNoContent(HttpResponse):
    status_code = 204

class HttpResponseUnprocessableEntity(HttpResponse):
    status_code = 422

class HttpResponseUnauthorized(HttpResponse):
    status_code = 401

#
# response_json functions
#
def response_json_forbidden(dict_in):
    return HttpResponseForbidden(json.dumps(dict_in, default=fallback_decoder), content_type='application/json')

def response_json_not_found(dict_in):
    return HttpResponseNotFound(json.dumps(dict_in, default=fallback_decoder), content_type='application/json')

def response_json_unprocessable_entity(dict_in):
    return HttpResponseUnprocessableEntity(json.dumps(dict_in, default=fallback_decoder), content_type='application/json')

def response_json_unauthorized(dict_in):
    return HttpResponseUnauthorized(json.dumps(dict_in, default=fallback_decoder), content_type='application/json')

#
# response_error functions  (these call the response_json functions)
#
def response_error_not_found(message):
    response = {
        KEY_RESULT: {
            KEY_CODE: VALUE_ERROR,
            KEY_MESSAGE: message
        }
    }
    return response_json_not_found(response)

def response_error_unprocessable_entity(message):
    response = {
        KEY_RESULT: {
            KEY_CODE: VALUE_ERROR,
            KEY_MESSAGE: message
        }
    }
    return response_json_unprocessable_entity(response)

def response_error_forbidden(message):
    response = {
        KEY_RESULT: {
            KEY_CODE: VALUE_ERROR,
            KEY_MESSAGE: message
        }
    }
    return response_json_forbidden(response)

def response_error_unauthorized(message):
    response = {
        KEY_RESULT: {
            KEY_CODE: VALUE_ERROR,
            KEY_MESSAGE: message
        }
    }
    return response_json_unauthorized(response)
