from rest_framework import serializers

from apps.accounts.models import User
from apps.companies.models import Company

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


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
    
# ------------------------------------------------------------------


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email, is_deleted=False)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                "email": "Invalid email or password."
            })

        user = authenticate(username=user.username, password=password)

        if not user:
            raise serializers.ValidationError({
                "password": "Invalid email or password."
            })

        if not user.is_active:
            raise serializers.ValidationError({
                "account": "This account is inactive."
            })

        refresh = RefreshToken.for_user(user)

        attrs["user"] = user
        attrs["refresh"] = str(refresh)
        attrs["access"] = str(refresh.access_token)

        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    company = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "company",
            "is_active",
            "created_at",
        ]

    def get_company(self, obj):
        if not obj.company:
            return None

        return {
            "id": obj.company.id,
            "name": obj.company.name,
            "slug": obj.company.slug,
            "email": obj.company.email,
        }
    
class UserListSerializer(serializers.ModelSerializer):
    company = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "company",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
        ]

    def get_company(self, obj):
        if not obj.company:
            return None

        return {
            "id": obj.company.id,
            "name": obj.company.name,
            "slug": obj.company.slug,
            "email": obj.company.email,
        }

# ------------------------------------------------------------------

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "confirm_password",
            "role",
            "is_active",
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("User with this username already exists.")
        return value

    def validate_role(self, value):
        allowed_roles = [
            User.RoleChoices.MANAGER,
            User.RoleChoices.EMPLOYEE,
        ]

        if value not in allowed_roles:
            raise serializers.ValidationError(
                "Admin can create only Manager or Employee users."
            )

        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Password and confirm password do not match."
            })

        request = self.context.get("request")

        if not request or not request.user.company:
            raise serializers.ValidationError({
                "company": "Logged-in admin must belong to a company."
            })

        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")

        request = self.context.get("request")
        company = request.user.company

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            role=validated_data["role"],
            company=company,
            is_active=validated_data.get("is_active", True),
        )

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "role",
            "password",
            "is_active",
        ]

    def validate_email(self, value):
        user = self.instance

        if User.objects.exclude(id=user.id).filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")

        return value

    def validate_username(self, value):
        user = self.instance

        if User.objects.exclude(id=user.id).filter(username=value).exists():
            raise serializers.ValidationError("User with this username already exists.")

        return value

    def validate_role(self, value):
        allowed_roles = [
            User.RoleChoices.MANAGER,
            User.RoleChoices.EMPLOYEE,
        ]

        if value not in allowed_roles:
            raise serializers.ValidationError(
                "User role can be updated only to Manager or Employee."
            )

        return value

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance