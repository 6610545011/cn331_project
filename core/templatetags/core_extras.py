# core/templatetags/core_extras.py
from django import template
from django.utils.text import slugify as django_slugify

register = template.Library()

@register.filter(name='unicode_slugify')
def unicode_slugify(value):
    """A version of slugify that allows unicode characters."""
    return django_slugify(value, allow_unicode=True)