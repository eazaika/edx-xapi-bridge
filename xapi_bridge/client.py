"""xAPI Client to send payload data."""


from tincan.remote_lrs import RemoteLRS

from xapi_bridge import settings


# TODO: wrap RemoteLRS with some custom exception handling
# TODO: logging

kw = {
    'endpoint': settings.LRS_ENDPOINT,
}
if settings.LRS_BASICAUTH_HASH:
    kw['auth'] = settings.LRS_BASICAUTH_HASH
else:
    kw['username'] = settings.LRS_USERNAME
    kw['password'] = settings.LRS_PASSWORD

# RemoteLRS will use auth if passed otherwise BasicAuth with un/pw
import pdb; pdb.set_trace()
lrs = RemoteLRS(**kw)
