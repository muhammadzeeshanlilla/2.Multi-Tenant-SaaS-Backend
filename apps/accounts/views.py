from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.accounts.serializers import (
    CompanyRegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
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