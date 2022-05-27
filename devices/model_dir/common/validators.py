from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_port_range(port: int):
    error = ValidationError(_('%(port)s outside of port range 1001-65535'), params={'port': port})
    if port > 65535:
        raise error
    if port < 1001:
        raise error
