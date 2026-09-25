from django.db import transaction
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework import serializers as drf_serializers
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer

from apps.accounts.models import User
from apps.accounts.permissions import IsAdmin, IsAdminOrManager
from apps.accounts.serializers import (
    CompanyRegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
    UserListSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    LogoutSerializer,
)

from apps.audit.models import AuditLog
from apps.audit.utils import create_audit_log


registration_response = inline_serializer(
    name="CompanyRegistrationResponse",
    fields={
        "success": drf_serializers.BooleanField(),
        "message": drf_serializers.CharField(),
        "data": drf_serializers.DictField(),
    },
)
login_response = inline_serializer(
    name="LoginResponse",
    fields={
        "success": drf_serializers.BooleanField(),
        "message": drf_serializers.CharField(),
        "data": drf_serializers.DictField(),
    },
)
profile_response = inline_serializer(
    name="CurrentUserResponse",
    fields={
        "success": drf_serializers.BooleanField(),
        "message": drf_serializers.CharField(),
        "data": UserProfileSerializer(),
    },
)
message_response = inline_serializer(
    name="SuccessMessageResponse",
    fields={
        "success": drf_serializers.BooleanField(),
        "message": drf_serializers.CharField(),
    },
)


class CompanyRegisterAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = CompanyRegisterSerializer

    @extend_schema(
        summary="Register a company and initial administrator",
        responses={
            201: registration_response,
            400: OpenApiResponse(description="Registration validation failed."),
            429: OpenApiResponse(description="Registration rate limit exceeded."),
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            try:
                result = serializer.save()
            except ValidationError as exc:
                return Response(
                    {
                        "success": False,
                        "message": "Company registration failed.",
                        "errors": exc.detail,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            company = result["company"]
            admin_user = result["admin_user"]

            return Response(
                {
                    "success": True,
                    "message": "Company registered successfully.",
                    "data": {
                        "company": {
                            "id": company.id,
                            "name": company.name,
                            "slug": company.slug,
                            "email": company.email,
                            "phone": company.phone,
                            "address": company.address,
                        },
                        "admin": {
                            "id": admin_user.id,
                            "username": admin_user.username,
                            "email": admin_user.email,
                            "role": admin_user.role,
                        },
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "success": False,
                "message": "Company registration failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        summary="Authenticate with email and password",
        responses={
            200: login_response,
            400: OpenApiResponse(description="Invalid credentials or unavailable account."),
            429: OpenApiResponse(description="Login rate limit exceeded."),
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]

            create_audit_log(
                request=request,
                action=AuditLog.ActionChoices.USER_LOGIN,
                object_type="User",
                object_id=user.id,
                description=f"{user.username} logged in successfully.",
                user=user,
            )

            return Response(
                {
                    "success": True,
                    "message": "Login successful.",
                    "data": {
                        "user": UserProfileSerializer(user).data,
                        "tokens": {
                            "refresh": serializer.validated_data["refresh"],
                            "access": serializer.validated_data["access"],
                        },
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "message": "Login failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class MeAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    @extend_schema(
        summary="Get the authenticated user, role, and company",
        responses={200: profile_response},
    )
    def get(self, request):
        serializer = self.get_serializer(request.user)

        return Response(
            {
                "success": True,
                "message": "User profile fetched successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(
        summary="Blacklist the authenticated user's refresh token",
        responses={
            200: message_response,
            400: OpenApiResponse(description="Invalid refresh token."),
        },
    )
    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Logout failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            serializer.save()

            create_audit_log(
                request=request,
                action=AuditLog.ActionChoices.USER_LOGOUT,
                object_type="User",
                object_id=request.user.id,
                description=f"{request.user.username} logged out successfully.",
            )

        return Response(
            {
                "success": True,
                "message": "Logout successful.",
            },
            status=status.HTTP_200_OK,
        )


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    queryset = User.objects.none()

    def get_permissions(self):
        if self.action == "list":
            return [IsAdminOrManager()]

        return [IsAdmin()]

    def get_queryset(self):
        return User.objects.filter(
            company=self.request.user.company,
            is_deleted=False,
        ).select_related("company").order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer

        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer

        return UserListSerializer

    def list(self, request, *args, **kwargs):
        users = self.get_queryset()
        page = self.paginate_queryset(users)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            self.paginator.response_message = "Users fetched successfully."
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(users, many=True)

        return Response(
            {
                "success": True,
                "message": "Users fetched successfully.",
                "count": users.count(),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            user = serializer.save()

            create_audit_log(
                request=request,
                action=AuditLog.ActionChoices.USER_CREATED,
                object_type="User",
                object_id=user.id,
                description=f"User {user.username} was created by {request.user.username}.",
            )

            return Response(
                {
                    "success": True,
                    "message": "User created successfully.",
                    "data": UserListSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "success": False,
                "message": "User creation failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)

        return Response(
            {
                "success": True,
                "message": "User fetched successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        user = self.get_object()

        if user.role == User.RoleChoices.ADMIN:
            return Response(
                {
                    "success": False,
                    "message": "Admin user cannot be updated from this API.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(
            user,
            data=request.data,
            partial=False,
        )

        if serializer.is_valid():
            updated_user = serializer.save()

            create_audit_log(
                request=request,
                action=AuditLog.ActionChoices.USER_UPDATED,
                object_type="User",
                object_id=updated_user.id,
                description=f"User {updated_user.username} was updated by {request.user.username}.",
            )

            return Response(
                {
                    "success": True,
                    "message": "User updated successfully.",
                    "data": UserListSerializer(updated_user).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "message": "User update failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()

        if user.role == User.RoleChoices.ADMIN:
            return Response(
                {
                    "success": False,
                    "message": "Admin user cannot be updated from this API.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(
            user,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            updated_user = serializer.save()

            create_audit_log(
                request=request,
                action=AuditLog.ActionChoices.USER_UPDATED,
                object_type="User",
                object_id=updated_user.id,
                description=f"User {updated_user.username} was updated by {request.user.username}.",
            )

            return Response(
                {
                    "success": True,
                    "message": "User updated successfully.",
                    "data": UserListSerializer(updated_user).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "message": "User update failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()

        if user.id == request.user.id:
            return Response(
                {
                    "success": False,
                    "message": "You cannot delete your own account.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.role == User.RoleChoices.ADMIN:
            return Response(
                {
                    "success": False,
                    "message": "Admin user cannot be deleted from this API.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_deleted = True
        user.is_active = False
        user.save()

        create_audit_log(
            request=request,
            action=AuditLog.ActionChoices.USER_DELETED,
            object_type="User",
            object_id=user.id,
            description=f"User {user.username} was deleted by {request.user.username}.",
        )

        return Response(
            {
                "success": True,
                "message": "User deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        user = User.objects.filter(
            id=pk,
            company=request.user.company,
            is_deleted=True,
        ).first()

        if not user:
            return Response(
                {
                    "success": False,
                    "message": "Deleted user not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        user.is_deleted = False
        user.is_active = True
        user.save()

        create_audit_log(
            request=request,
            action=AuditLog.ActionChoices.USER_RESTORED,
            object_type="User",
            object_id=user.id,
            description=f"User {user.username} was restored by {request.user.username}.",
        )

        return Response(
            {
                "success": True,
                "message": "User restored successfully.",
                "data": UserListSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )
