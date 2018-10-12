"""xAPI Client to send payload data."""


from tincan.remote_lrs import RemoteLRS

from xapi_bridge import settings


# TODO: wrap RemoteLRS with some custom exception handling
# TODO: logging

kw = {
    'endpoint': settings.LRS_ENDPOINT,
    'username': settings.LRS_USERNAME,
    'password': settings.LRS_PASSWORD
}
if settings.LRS_BASICAUTH_HASH:
    kw['auth'] = settings.LRS_BASICAUTH_HASH

# RemoteLRS will use auth if passed otherwise BasicAuth with un/pw

lrs = RemoteLRS(**kw)
