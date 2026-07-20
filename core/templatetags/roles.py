from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):

    if user.is_superuser:
        return True

    return user.groups.filter(
        name=group_name
    ).exists()


@register.filter
def has_any_group(user, group_names):

    if user.is_superuser:
        return True

    groups = [
        name.strip()
        for name in group_names.split(",")
    ]

    return user.groups.filter(
        name__in=groups
    ).exists()
