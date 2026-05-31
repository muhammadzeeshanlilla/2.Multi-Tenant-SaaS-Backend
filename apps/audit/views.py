from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.accounts.permissions import IsAdmin


class AuditLogListAPIView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        logs = AuditLog.objects.filter(
            company=request.user.company
        ).order_by("-created_at")

        serializer = AuditLogSerializer(logs, many=True)

        return Response(
            {
                "success": True,
                "message": "Audit logs fetched successfully.",
                "count": logs.count(),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )