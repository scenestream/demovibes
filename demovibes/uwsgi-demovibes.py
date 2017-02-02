import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'demovibes.settings'

sys.path.append('/home/demovibes/demovibes')
sys.path.append('/home/demovibes/demovibes/demovibes')


import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
applications = {'': application}
