from django.shortcuts import render


def permission_denied_view(
    request,
    exception
):
    return render(
        request,
        "errors/403.html",
        status=403,
    )
