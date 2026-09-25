from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ActiveCompanyJWTAuthentication(JWTAuthentication):
    """Reject JWTs for users whose company has been deactivated."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)

        if user.company_id and not user.company.is_active:
            raise AuthenticationFailed(
                "User account is unavailable.",
                code="company_inactive",
            )

        return user


class ActiveCompanyJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "apps.accounts.authentication.ActiveCompanyJWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
