from rest_framework import permissions

# assumes you have:
# from django.contrib.auth.models import User as AuthUser
# and your profile model: from .models import User as Profile, Employee, Order

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)

class IsEmployee(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and hasattr(request.user, 'profile')
            and hasattr(request.user.profile, 'employee')
            and request.user.profile.employee.role == 'employee'
        )

class IsSelfProfile(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # obj is a Profile instance
        return bool(request.user and hasattr(request.user, 'profile') and obj.id == request.user.profile.id)

class IsSelfEmployee(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # obj is an Employee instance
        return bool(
            request.user
            and hasattr(request.user, 'profile')
            and hasattr(request.user.profile, 'employee')
            and obj.id == request.user.profile.employee.id
        )

class MenuAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        # GET: anyone
        if request.method in permissions.SAFE_METHODS:
            return True
        # POST/PUT/DELETE: admin or employee
        return bool(
            request.user
            and (request.user.is_staff or IsEmployee().has_permission(request, view))
        )

class OrderListCreate(permissions.BasePermission):
    def has_permission(self, request, view):
        # GET: must be authenticated to see own or all
        if request.method == 'GET':
            return bool(request.user and request.user.is_authenticated)
        # POST: any authenticated user
        if request.method == 'POST':
            return bool(request.user and request.user.is_authenticated)
        return False

class OrderObjectAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # obj is an Order instance
        profile = getattr(request.user, 'profile', None)
        is_emp = IsEmployee().has_permission(request, view)
        # GET
        if request.method in permissions.SAFE_METHODS:
            if request.user.is_staff or is_emp:
                return True
            return obj.user_id == profile.id
        # PUT: admin or employee
        if request.method == 'PUT':
            return bool(request.user.is_staff or is_emp)
        # DELETE: admin only
        if request.method == 'DELETE':
            return bool(request.user.is_staff)
        return False
