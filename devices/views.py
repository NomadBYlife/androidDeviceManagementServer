from concurrent.futures import ThreadPoolExecutor
from django.http import HttpResponse, HttpRequest
from django.views.decorators import http
from django.views.decorators.csrf import csrf_exempt

from .views_dir import device_index
from .views_dir import device_detail
from .views_dir import device_claim
from .views_dir import device_release
from .views_dir import device_function
from .views_dir import function_index

the_tpe = ThreadPoolExecutor(max_workers=5)


# this should be unused
def _not_implemented(request: HttpRequest, *args, **kwargs):  # can be unused # pragma: no cover
    return HttpResponse("\nNot implemented\n", status=200, reason="OK")


@csrf_exempt
@http.require_http_methods(['GET'])
def index(request: HttpRequest):
    method_switch = {
        'GET': device_index.get
    }
    return method_switch.get(request.method, _not_implemented)(request)


@csrf_exempt
@http.require_http_methods(['GET'])
def detail(request: HttpRequest, **kwargs):
    method_switch = {
        'GET': device_detail.get
    }
    return method_switch.get(request.method, _not_implemented)(request, **kwargs)


@csrf_exempt
@http.require_http_methods(['GET'])
def claim(request: HttpRequest, **kwargs):
    method_switch = {
        'GET': device_claim.get
    }
    return method_switch.get(request.method, _not_implemented)(request, **kwargs)


@csrf_exempt
@http.require_http_methods(['GET'])
def release(request: HttpRequest, **kwargs):
    method_switch = {
        'GET': device_release.get
    }
    return method_switch.get(request.method, _not_implemented)(request, **{'the_tpe': the_tpe, **kwargs})


@csrf_exempt
@http.require_http_methods(['GET'])
def function_call(request: HttpRequest, **kwargs):
    method_switch = {
        'GET': device_function.get
    }
    return method_switch.get(request.method, _not_implemented)(request, **{'the_tpe': the_tpe, **kwargs})


"""
@csrf_exempt
@http.require_http_methods(['GET'])
def function_detail(request: HttpRequest, **kwargs):
    method_switch = {
        'GET': function_index.get
    }
    return method_switch.get(request.method, _not_implemented)(request, **kwargs)
"""
