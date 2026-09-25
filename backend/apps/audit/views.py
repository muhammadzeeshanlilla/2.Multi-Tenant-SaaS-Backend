from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework import serializers as drf_serializers
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.accounts.permissions import IsAdmin


audit_list_response = inline_serializer(
    name="PaginatedAuditLogResponse",
    fields={
        "success": drf_serializers.BooleanField(),
        "message": drf_serializers.CharField(),
        "count": drf_serializers.IntegerField(),
        "next": drf_serializers.URLField(allow_null=True),
        "previous": drf_serializers.URLField(allow_null=True),
        "data": AuditLogSerializer(many=True),
    },
)


class AuditLogListAPIView(GenericAPIView):
    permission_classes = [IsAdmin]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        logs = AuditLog.objects.filter(
            company=self.request.user.company
        ).select_related("company", "user").order_by("-created_at")

        action = self.request.query_params.get("action")
        if action:
            valid_actions = {choice for choice, _ in AuditLog.ActionChoices.choices}
            if action not in valid_actions:
                raise ValidationError({"action": "Invalid audit action."})
            logs = logs.filter(action=action)

        return logs

    @extend_schema(
        summary="List audit logs for the authenticated Admin's company",
        parameters=[
            OpenApiParameter(
                name="action",
                type=str,
                enum=[choice for choice, _ in AuditLog.ActionChoices.choices],
                description="Filter by audit action.",
            ),
        ],
        responses={200: audit_list_response},
    )
    def get(self, request):
        logs = self.get_queryset()
        page = self.paginate_queryset(logs)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            self.paginator.response_message = "Audit logs fetched successfully."
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(logs, many=True)

        return Response(
            {
                "success": True,
                "message": "Audit logs fetched successfully.",
                "count": logs.count(),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
