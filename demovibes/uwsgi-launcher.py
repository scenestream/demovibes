import os
import sys

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
SITE_ROOT = os.path.dirname(SITE_ROOT)

sys.path.append(SITE_ROOT)
sys.path.append(os.path.join(SITE_ROOT, "demovibes"))

os.environ['DJANGO_SETTINGS_MODULE'] = 'demovibes.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

applications = {'/':application}
