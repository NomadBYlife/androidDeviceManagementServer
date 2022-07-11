from django.urls import re_path

from .consumers import MainConsumer

websocket_urlpatterns = [
    re_path(r'ws/socket_client/$', MainConsumer.as_asgi()),
]