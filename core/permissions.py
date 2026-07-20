from functools import wraps
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


logger = logging.getLogger(__name__)


def group_required(*group_names):
    """
    Restrict access to specific Django Groups.

    Example:

    @group_required("Admin")
    @group_required("Admin", "Manager")
    """

    def decorator(view_func):

        @login_required
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):

            user = request.user

            if user.is_superuser:
                return view_func(
                    request,
                    *args,
                    **kwargs
                )

            if user.groups.filter(
                name__in=group_names
            ).exists():

                return view_func(
                    request,
                    *args,
                    **kwargs
                )

            logger.warning(
                "Permission denied. "
                f"User={user.username} "
                f"Groups={list(user.groups.values_list('name', flat=True))} "
                f"Path={request.path}"
            )

            raise PermissionDenied(
                "You do not have permission to access this resource."
            )

        return wrapped_view

    return decorator


def is_admin(user):

    return (
        user.is_superuser
        or user.groups.filter(
            name="Admin"
        ).exists()
    )


def is_manager(user):

    return user.groups.filter(
        name="Manager"
    ).exists()


def is_cashier(user):

    return user.groups.filter(
        name="Cashier"
    ).exists()


def is_kitchen(user):

    return user.groups.filter(
        name="Kitchen"
    ).exists()


def is_waiter(user):

    return user.groups.filter(
        name="Waiter"
    ).exists()
