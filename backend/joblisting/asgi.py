import os
from django.core.asgi import get_asgi_application

# Set the default settings module for the 'joblisting' project.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'joblisting.settings')

application = get_asgi_application()
