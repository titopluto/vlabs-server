from django.conf import settings

from datetime import datetime, timedelta


#JWT CUSTOM RESPONSE
def jwt_response_payload_handler(token, user=None, request=None):
    return {
        'token': token,
        'hours': (settings.JWT_AUTH['JWT_EXPIRATION_DELTA'].seconds) / 3600.0
    }
