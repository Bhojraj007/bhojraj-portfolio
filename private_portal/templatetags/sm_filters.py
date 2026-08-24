from django import template

register = template.Library()

@register.filter(name='get_field')
def get_field(obj, field_name):
    """Get a field value from a model instance by field name."""
    try:
        return getattr(obj, field_name, '')
    except Exception:
        return ''
