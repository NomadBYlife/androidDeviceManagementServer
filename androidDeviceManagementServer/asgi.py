import os

import django
from channels.auth import AuthMiddlewareStack
from channels.http import AsgiHandler
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

import socket_client.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

application = ProtocolTypeRouter({
  "http": AsgiHandler(),
  "websocket": AllowedHostsOriginValidator(
          AuthMiddlewareStack(
              URLRouter(
                  socket_client.routing.websocket_urlpatterns
              )
          )
      ),
  # Just HTTP for now. (We can add other protocols later.)
})