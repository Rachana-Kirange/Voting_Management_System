from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """Decorator that allows only authenticated users with role 'admin' or is_superuser."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            messages.error(request, 'You must be logged in to access this page')
            return redirect('login')

        # check role or is_superuser
        if getattr(user, 'role', None) == 'admin' or user.is_superuser:
            return view_func(request, *args, **kwargs)

        messages.error(request, 'Administrator access required')
        return redirect('users_home')

    return _wrapped
