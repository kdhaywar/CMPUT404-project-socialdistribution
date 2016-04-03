import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

from whitenoise.django import DjangoWhiteNoise

'''
dj-static allows you to properly serve static assets 
from production with a WSGI server: https://pypi.python.org/pypi/dj-static
'''
from dj_static import Cling

application = Cling(get_wsgi_application())
application = DjangoWhiteNoise(application)
