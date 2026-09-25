from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        if view.__class__.__name__ != "LoginAPIView":
            return None

        email = request.data.get("email", "")
        ident = self.get_ident(request)

        return self.cache_format % {
            "scope": self.scope,
            "ident": f"{ident}:{email}",
        }


class CompanyRegisterRateThrottle(SimpleRateThrottle):
    scope = "company_register"

    def get_cache_key(self, request, view):
        if view.__class__.__name__ != "CompanyRegisterAPIView":
            return None

        ident = self.get_ident(request)

        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }