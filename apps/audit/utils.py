from apps.audit.models import AuditLog


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip


def create_audit_log(
    request,
    action,
    object_type=None,
    object_id=None,
    description=None,
):
    user = request.user if request.user and request.user.is_authenticated else None
    company = user.company if user else None

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