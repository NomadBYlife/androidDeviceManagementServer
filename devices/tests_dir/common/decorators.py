from json import JSONDecoder

from django.http import JsonResponse, HttpResponse

from log_config import set_log_level

log = set_log_level()


def do_rest_json(rest_fun, url: str, body=None):
    def decorator(fun):
        def wrapper(self, **kwargs):
            response: JsonResponse = rest_fun(url, data=body)
            body_as_dict = JSONDecoder().decode(response.content.decode())
            fun(self, response, body_as_dict, **kwargs)

        return wrapper

    return decorator


def do_rest_http(rest_fun, url: str):
    def decorator(fun):
        def wrapper(self, **kwargs):
            response: HttpResponse = rest_fun(url)
            fun(self, response, **kwargs)

        return wrapper

    return decorator
