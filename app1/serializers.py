from rest_framework import serializers
from .models import User, Employee, MenuItem, Order, OrderMenu
class UserSerializer(serializers.ModelSerializer):
    # ahora password es lectura/escritura
    password = serializers.CharField()

    class Meta:
        model = User
        fields = ['id', 'name', 'address', 'contact', 'buyer_score', 'password']

    def create(self, validated_data):
        raw_password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(raw_password)
        user.save()
        # guardamos para la representación
        self._raw_password = raw_password
        return user

    def update(self, instance, validated_data):
        raw_password = validated_data.pop('password', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if raw_password:
            instance.set_password(raw_password)
            # si existe Employee relacionado, sincronizamos su secret_password
            try:
                emp = instance.employee
                emp.secret_password = raw_password
                emp.save()
            except Employee.DoesNotExist:
                pass
            self._raw_password = raw_password
        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # si acabamos de crear/actualizar, inyectamos el raw_password
        if hasattr(self, '_raw_password'):
            data['password'] = self._raw_password
        return data


class EmployeeSerializer(serializers.ModelSerializer):
    # agregamos campo write-only para la contraseña
    password = serializers.CharField(write_only=True)
    # mostramos también el UserSerializer con su password ya sincronizado
    user = UserSerializer(read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'user', 'password', 'image', 'role', 'description']

    def create(self, validated_data):
        raw_pass = validated_data.pop('password')
        # creamos o actualizamos el User vinculado
        user_data = {
            'name': self.context['request'].data.get('name'),
            'address': self.context['request'].data.get('address'),
            'contact': self.context['request'].data.get('contact'),
            'buyer_score': self.context['request'].data.get('buyer_score', 0),
            'password': raw_pass
        }
        user_ser = UserSerializer(data=user_data)
        user_ser.is_valid(raise_exception=True)
        user = user_ser.save()
        emp = Employee.objects.create(
            user=user,
            image=validated_data.get('image'),
            role=validated_data.get('role'),
            description=validated_data.get('description'),
        )
        return emp
    
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