from django.http import HttpRequest


def safe_get_dict_item(target: dict, item_name: str, default: str) -> str:
    if item_name in target:
        return target[item_name]
    else:
        return str(default)


def log_request(request: HttpRequest, msg: str) -> str:
    # Django doesn't populate this value in the development server but a production WSGI server like apache would
    client_port = safe_get_dict_item(request.META, 'REMOTE_PORT', 'unk')
    # Django doesn't populate the following values during testing
    content_type = safe_get_dict_item(request.META, 'CONTENT_TYPE', 'django/hides/info')
    http_user_agent = safe_get_dict_item(request.META, 'HTTP_USER_AGENT', 'django/hides/info')
    http_accept = safe_get_dict_item(request.META, 'HTTP_ACCEPT', 'django/hides/info')
    return ('{}\n    {}\n    {}\n      {}'.format(
        'Request from: %s:%s' % (request.META['REMOTE_ADDR'], client_port),
        '%s %s' % (request.method, str(request.get_raw_uri())),
        'Content Type: %s    User Agent: %s    HTTP accept: %s' % (content_type, http_user_agent, http_accept),
        msg
    ))
