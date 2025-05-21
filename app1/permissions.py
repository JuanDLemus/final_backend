from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsEmployee(BasePermission):
    """
    Permission for any view-level check: is the user authenticated
    and has an Employee record with role 'Empleado'?
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and hasattr(user, 'employee')
        )

    def has_object_permission(self, request, view, obj):
        # by default, same as view-level check
        return self.has_permission(request, view)
    
class IsAdmin(BasePermission):
    """
    Permission for any view-level check: is the user authenticated
    and has an Employee record with role 'Empleado'?
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and hasattr(user, 'employee')
            and user.employee.role == 'Admin'
        )

    def has_object_permission(self, request, view, obj):
        # by default, same as view-level check
        return self.has_permission(request, view)

class IsSelf(BasePermission):
    """
    View-level: only allow if user is authenticated.
    Object-level: only if the target obj.id matches request.user.id.
    Expects obj to be a User instance.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user
            and request.user.is_authenticated
            and obj.id == request.user.id
        )
    
class IsMenu(BasePermission):
    """
    - SAFE_METHODS (GET, HEAD, OPTIONS): allow anyone
    - Other methods: only allow if user is an authenticated Employee
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        # non‐SAFE: require IsEmployee
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and hasattr(user, 'employee')
            and user.employee.role == 'Empleado'
        )
    
class IsOrder(BasePermission):
    """
    - GET: Users see their own orders; employees see all
    - POST: Any authenticated user can create an order
    - PUT: Only authenticated employees can update (e.g. change status)
    - DELETE: Only Admin employees can delete
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if request.method == 'POST':
            return True  # Any authenticated user can create

        if request.method in SAFE_METHODS:
            return True  # Filter logic is handled in the view

        if request.method == 'PUT':
            return hasattr(user, 'employee')

        if request.method == 'DELETE':
            return hasattr(user, 'employee') and user.employee.role == 'Admin'

        return False
    
    
class IsRegistration(BasePermission):
    """
    Allow anyone to POST (register), but restrict GET to employees only.
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            return True  # Anyone can register
        elif request.method == 'GET':
            return request.user and request.user.is_authenticated and hasattr(request.user, 'employee')
        return False