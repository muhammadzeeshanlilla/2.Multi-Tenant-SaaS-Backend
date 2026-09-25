from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Allows access only to company Admin users.
    """

    message = "Only admin users are allowed to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
            and not request.user.is_deleted
        )


class IsManager(BasePermission):
    """
    Allows access only to company Manager users.
    """

    message = "Only manager users are allowed to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "MANAGER"
            and not request.user.is_deleted
        )


class IsEmployee(BasePermission):
    """
    Allows access only to company Employee users.
    """

    message = "Only employee users are allowed to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "EMPLOYEE"
            and not request.user.is_deleted
        )


class IsAdminOrManager(BasePermission):
    """
    Allows access to Admin and Manager users.
    Useful for project and task management.
    """

    message = "Only admin or manager users are allowed to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["ADMIN", "MANAGER"]
            and not request.user.is_deleted
        )


class IsCompanyUser(BasePermission):
    """
    Allows access only if the object belongs to the same company as request.user.
    This is important for tenant isolation.
    """

    message = "You do not have permission to access this company's data."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_deleted:
            return False

        if not hasattr(obj, "company"):
            return False

        return obj.company == request.user.company


class IsOwnerOrAdmin(BasePermission):
    """
    Allows access if:
    - User is Admin of the same company
    - OR object belongs to the same user
    Useful for user profile related operations.
    """

    message = "You do not have permission to access this object."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_deleted:
            return False

        if request.user.role == "ADMIN" and obj.company == request.user.company:
            return True

        return obj == request.user  