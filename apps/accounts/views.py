from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework import viewsets
from rest_framework.decorators import action
from apps.accounts.models import User
from apps.accounts.permissions import IsAdmin

from apps.accounts.serializers import (
    CompanyRegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
    UserListSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)


class CompanyRegisterAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CompanyRegisterSerializer(data=request.data)

        if serializer.is_valid():
            result = serializer.save()

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

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]

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


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)

        return Response(
            {
                "success": True,
                "message": "User profile fetched successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )   
    
# ---------------------
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return User.objects.filter(
            company=self.request.user.company,
            is_deleted=False,
        ).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer

        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer

        return UserListSerializer

    def list(self, request, *args, **kwargs):
        users = self.get_queryset()
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
            context={"request": request}
        )

        if serializer.is_valid():
            user = serializer.save()

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

        return Response(
            {
                "success": True,
                "message": "User restored successfully.",
                "data": UserListSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )