from rest_framework import serializers
from django.contrib.auth.models import User as DjangoUser
from .models import User, Employee, MenuItem, Order, OrderMenu

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DjangoUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class User2Serializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'address', 'contact', 'buyer_score', 'password']

class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Employee
        fields = ['id', 'user', 'secret_password', 'image', 'role', 'description']

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'image_link', 'name', 'description', 'ingredients', 'price', 'awareness', 'category', 'calories']

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'user', 'datetime', 'total_price', 'status']

class OrderMenuSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    menu_item = MenuItemSerializer(read_only=True)
    class Meta:
        model = OrderMenu
        fields = ['order', 'menu_item', 'quantity']