"""
Add xApiProcessor to event tracking backends' list.
"""
__version__ = "0.0.1"

from django.conf import settings as django_settings

from xapi_bridge import processor
from xapi_bridge.settings import OPENEDX_XAPI_TRACKING_BACKENDS, OPENEDX_XAPI_TRACKING_PROCESSOR


default_app_config = 'xapi_bridge.apps.XApiTrackingConfig'


if hasattr(django_settings, 'EVENT_TRACKING_BACKENDS'):
    django_settings.EVENT_TRACKING_BACKENDS['tracking_logs']['OPTIONS']['processors'] += [
        {'ENGINE': OPENEDX_XAPI_TRACKING_PROCESSOR}
    ]

if hasattr(django_settings, 'TRACKING_BACKENDS'):
    django_settings.TRACKING_BACKENDS = OPENEDX_XAPI_TRACKING_BACKENDS
