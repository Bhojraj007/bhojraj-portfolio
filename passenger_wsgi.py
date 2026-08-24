import os
import sys

# Set up paths for cPanel / CloudLinux Python App (Phusion Passenger)
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set Django Settings Module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_site.settings")

# WSGI Application Handler
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
