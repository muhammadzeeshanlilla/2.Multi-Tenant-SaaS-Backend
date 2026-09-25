from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_project_assignment_email(
    user_email,
    username,
    project_name,
    assigned_by,
    assigned_by_role,
):
    subject = f"You have been assigned to project: {project_name}"

    message = f"""
Hello {username},

You have been assigned to a project.

Project: {project_name}
Assigned by: {assigned_by}
Assigned by role: {assigned_by_role}

Please login to the TenantFlow system and check your assigned project.

Regards,
TenantFlow System
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )

    return f"Project assignment email sent to {user_email}"


@shared_task
def send_task_assignment_email(
    user_email,
    username,
    task_title,
    project_name,
    assigned_by,
    assigned_by_role,
):
    subject = f"New task assigned: {task_title}"

    message = f"""
Hello {username},

A new task has been assigned to you.

Task: {task_title}
Project: {project_name}
Assigned by: {assigned_by}
Assigned by role: {assigned_by_role}

Please login to the TenantFlow system and review your task.

Regards,
TenantFlow System
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )

    return f"Task assignment email sent to {user_email}"