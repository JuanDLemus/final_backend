from rest_framework import serializers
from .models import User, Employee, MenuItem, Order, OrderMenu


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'address', 'contact', 'buyer_score', 'password']

    def create(self, validated_data):
        raw_password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(raw_password)
        user.save()
        return user

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