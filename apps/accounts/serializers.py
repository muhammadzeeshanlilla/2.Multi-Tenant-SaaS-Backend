from rest_framework import serializers

from apps.accounts.models import User
from apps.companies.models import Company


class CompanyRegisterSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=255)
    company_email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate_company_email(self, value):
        if Company.objects.filter(email=value).exists():
            raise serializers.ValidationError("Company with this email already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("User with this username already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Password and confirm password do not match."
            })
        return attrs

    def create(self, validated_data):
        company = Company.objects.create(
            name=validated_data["company_name"],
            email=validated_data["company_email"],
            phone=validated_data.get("phone", ""),
            address=validated_data.get("address", ""),
        )

        admin_user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            company=company,
            role=User.RoleChoices.ADMIN,
            is_staff=True,
        )

        return {
            "company": company,
            "admin_user": admin_user
        }