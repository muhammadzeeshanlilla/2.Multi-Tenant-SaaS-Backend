from apps.audit.models import AuditLog


def get_client_ip(request):
    """
    Get client IP address from request.
    Works for local development and reverse proxy environments.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip


def create_audit_log(
    request,
    action,
    object_type=None,
    object_id=None,
    description=None,
    user=None,
):
    """
    Create audit log for authenticated users only.
    Log is linked with the logged-in user's company.
    """

    if not request:
        return None

    user = user or getattr(request, "user", None)

    if not user or not user.is_authenticated:
        return None

    if getattr(user, "is_deleted", False):
        return None

    company = getattr(user, "company", None)

    if not company:
        return None

    return AuditLog.objects.create(
        company=company,
        user=user,
        action=action,
        object_type=object_type,
        object_id=object_id,
        description=description,
        ip_address=get_client_ip(request),
    )
