from django.urls import path, include, re_path
import notifications.urls

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('release/<device_key>/', views.release, name='release'),
    path('claim/<device_type>/', views.claim, name='claim'),
    path('function/<function_name>/<device_key>/', views.function_call, name='function_call'),
    path('detail/<device_key>/', views.detail, name='detail'),
    re_path('^inbox/notifications/', include(notifications.urls, namespace='notifications')),
    # path('debug/functions/index/', views.function_detail, name='function_detail'),
]
