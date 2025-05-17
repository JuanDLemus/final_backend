import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, get_list_or_404
from django.db import connection
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import authenticate
from .models import User, MenuItem, Order, Employee, OrderMenu
from .serializers import UserSerializer, EmployeeSerializer, MenuItemSerializer, OrderSerializer, OrderMenuSerializer
from django.contrib.auth.models import User as AuthUser
from .models import User as Profile, Employee, MenuItem, Order, OrderMenu
from .permissions import (
    IsAdmin, IsEmployee, IsSelfProfile, IsSelfEmployee,
    MenuAccess, OrderListCreate, OrderObjectAccess
)
#############################################################################################################################################################################################################################################################################################################################################################################################
@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    name = request.data.get('name')
    password = request.data.get('password')

    user = authenticate(username=name, password=password)
    if user is not None:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})
    else:
        return Response({"error": "Invalid credentials"}, status=400)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
#@permission_classes([IsAuthenticated])
@permission_classes([AllowAny])
def user_profile(request):
    data = UserSerializer(request.user).data
    return Response(
        {"user": data},
        status=status.HTTP_200_OK
    )
#############################################################################################################################################################################################################################################################################################################################################################################################
    
# Listar todos los usuarios o crear uno nuevo
@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
#@permission_classes([IsAdmin|IsEmployee])  # Solo admin o empleados pueden usar
@permission_classes([AllowAny])
def listar_o_crear_usuario(request):
    if request.method == 'GET':
        usuarios = User.objects.all()
        serializer = UserSerializer(usuarios, many=True)
        # No devolver password, porque está write_only, no aparece en serializer.data
        return Response(serializer.data)

    elif request.method == 'POST':
        password = request.data.get('password')
        if not password:
            return Response(
                {"error": "Password is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {"token": token.key, "user": serializer.data},
            status=status.HTTP_201_CREATED
        )

# Detalle, editar o eliminar un usuario
@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
#@permission_classes([IsSelfProfile|IsAdmin])  # El propio usuario o admin
@permission_classes([AllowAny])
def detalle_o_editar_o_eliminar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, pk=usuario_id)

    if request.method == 'GET':
        # Traer las órdenes y sus items como antes
        orders = Order.objects.filter(user=usuario)
        orders_data = []
        for order in orders:
            order_items = OrderMenu.objects.filter(order=order).select_related('menu_item')
            items_data = [
                {
                    'menu_item_id': om.menu_item.id if om.menu_item else None,
                    'menu_item_name': om.menu_item.name if om.menu_item else None,
                    'quantity': om.quantity,
                    'price_per_unit': om.menu_item.price if om.menu_item else None,
                    'subtotal': float(om.menu_item.price * om.quantity) if om.menu_item and om.menu_item.price else None
                } for om in order_items
            ]
            orders_data.append({
                'order_id': order.id,
                'datetime': order.datetime,
                'total_price': order.total_price,
                'status': order.status,
                'items': items_data
            })

        user_data = UserSerializer(usuario).data
        user_data['orders'] = orders_data

        return Response(user_data)

    elif request.method == 'PUT':
        serializer = UserSerializer(usuario, data=request.data, partial=True)
        if serializer.is_valid():
            # Importante: Si viene password, el serializer setea bien con set_password()
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        usuario.delete()
        return Response({'message': 'User deleted'}, status=status.HTTP_204_NO_CONTENT)
    
#############################################################################################################################################################################################################################################################################################################################################################################################
## List or create menu item
@csrf_exempt
#@permission_classes([MenuAccess])
@permission_classes([AllowAny])
@require_http_methods(["GET", "POST"])
def listar_o_crear_menu_item(request):
    if request.method == 'GET':
        menu_items = MenuItem.objects.all()
        data = [
            {
                'id': item.id,
                'image_link': item.image_link,
                'name': item.name,
                'description': item.description,
                'ingredients': item.ingredients,
                'price': item.price,
                'awareness': item.awareness,
                'category': item.category,
                'calories': item.calories
            } for item in menu_items
        ]
        return JsonResponse(data, safe=False)


    elif request.method == 'POST':
        data = json.loads(request.body)
        try:
            item = MenuItem(
                name=data.get('name'),
                description=data.get('description', ''),
                ingredients=data.get('ingredients', ''),
                price=data.get('price'),
                awareness=data.get('awareness', ''),
                category=data.get('category', ''),
                calories=data.get('calories'),
                image_link=data.get('image_link', '') 
            )
            item.save()
            return JsonResponse({'id': item.id, 'name': item.name, 'price': item.price, 'category': item.category, 'calories': item.calories, 'image_link': item.image_link}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
#@permission_classes([MenuAccess])
@permission_classes([AllowAny])
@require_http_methods(["GET", "PUT", "DELETE"])
def detalle_o_editar_o_eliminar_menu_item(request, menu_id):
    if request.method == 'GET':
        menu_item = get_object_or_404(MenuItem, pk=menu_id)

        # Calcular en cuántas órdenes aparece
        ordenes_count = OrderMenu.objects.filter(menu_item=menu_item).count()

        data = {
            'id': menu_item.id,
            'name': menu_item.name,
            'description': menu_item.description,
            'ingredients': menu_item.ingredients,
            'price': menu_item.price,
            'awareness': menu_item.awareness,
            'category': menu_item.category,
            'calories': menu_item.calories,
            'image_link': menu_item.image_link,
            'used_in_orders': ordenes_count 
        }
        return JsonResponse(data)

    elif request.method == 'PUT':
        menu_item = get_object_or_404(MenuItem, pk=menu_id)
        data = json.loads(request.body)
        if 'name' in data:
            menu_item.name = data['name']
        if 'description' in data:
            menu_item.description = data['description']
        if 'ingredients' in data:
            menu_item.ingredients = data['ingredients']
        if 'price' in data:
            menu_item.price = data['price']
        if 'awareness' in data:
            menu_item.awareness = data['awareness']
        if 'category' in data:
            menu_item.category = data['category']
        if 'calories' in data:
            menu_item.calories = data['calories']
        if 'image_link' in data:
            menu_item.image_link = data['image_link']
        menu_item.save()

        return JsonResponse({
            'id': menu_item.id,
            'name': menu_item.name,
            'description': menu_item.description,
            'ingredients': menu_item.ingredients,
            'price': menu_item.price,
            'awareness': menu_item.awareness,
            'category': menu_item.category,
            'calories': menu_item.calories,
            'image_link': menu_item.image_link
        })

    elif request.method == 'DELETE':
        menu_item = get_object_or_404(MenuItem, pk=menu_id)
        menu_item.delete()
        return JsonResponse({'message': 'Menu item deleted'})

#############################################################################################################################################################################################################################################################################################################################################################################################
# List or create employee
@csrf_exempt
#@permission_classes([IsAdmin])
@permission_classes([AllowAny])
@require_http_methods(["GET", "POST"])
def listar_o_crear_empleado(request):
    if request.method == 'GET':
        empleados = Employee.objects.select_related('user').all()
        data = [
            {
                'id': e.id,
                'user_id': e.user.id if e.user else None,
                'user_name': e.user.name if e.user else None,
                'password': e.secret_password,
                'image': e.image.url if e.image else None,
                'role': e.role,
                'description': e.description
            } for e in empleados
        ]
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        password = data.get('password')
        if not password:
            return JsonResponse({"error": "Password is required"}, status=400)

        user_data = {
            'name': data.get('name'),
            'address': data.get('address'),
            'contact': data.get('contact'),
            'buyer_score': data.get('buyer_score', 0),
            'password': password
        }
        user_serializer = UserSerializer(data=user_data)
        if not user_serializer.is_valid():
            return JsonResponse(user_serializer.errors, status=400)

        user = user_serializer.save()
        # Create token for the user
        token, _ = Token.objects.get_or_create(user=user)

        try:
            empleado = Employee(
                user=user,
                secret_password=data.get('password'),
                image=data.get('image'),
                role=data.get('role'),
                description=data.get('description')
            )
            empleado.save()

            return JsonResponse({
                'token': token.key,              # <-- token here
                'employee_id': empleado.id,
                'user_id': user.id,
                'name': user.name,
                'role': empleado.role
            }, status=201)
        except Exception as e:
            user.delete()
            return JsonResponse({'error': str(e)}, status=400)



# Update or delete employee
@csrf_exempt
#@permission_classes([IsSelfEmployee|IsAdmin])
@permission_classes([AllowAny])
@require_http_methods(["GET", "PUT", "DELETE"])
def detalle_o_editar_o_eliminar_empleado(request, empleado_id):
    if request.method == 'GET':
        empleado = get_object_or_404(Employee, pk=empleado_id)
        data = {
            'id': empleado.id,
            'user_id': empleado.user.id if empleado.user else None,
            'user_name': empleado.user.name if empleado.user else None,
            'password': empleado.secret_password,
            'image': empleado.image.url if empleado.image else None,
            'role': empleado.role,
            'description': empleado.description
        }
        return JsonResponse(data)


    elif request.method == 'PUT':
        empleado = get_object_or_404(Employee, pk=empleado_id)
        data = json.loads(request.body)
        if 'role' in data:
            empleado.role = data['role']
        if 'description' in data:
            empleado.description = data['description']
        empleado.save()
        return JsonResponse({'id': empleado.id, 'name': empleado.user.name, 'role': empleado.role})

    elif request.method == 'DELETE':
        empleado = get_object_or_404(Employee, pk=empleado_id)
        empleado.delete()
        return JsonResponse({'message': 'Employee deleted'})

#############################################################################################################################################################################################################################################################################################################################################################################################
# List or create order
@csrf_exempt
#@permission_classes([OrderListCreate])
@permission_classes([AllowAny])
@require_http_methods(["GET", "POST"])
def listar_o_crear_orden(request):
    if request.method == 'GET':
        orders = Order.objects.select_related('user').all()
        data = []
        for order in orders:
            order_items = OrderMenu.objects.filter(order=order).select_related('menu_item')
            items_data = [
                {
                    'menu_item_id': om.menu_item.id,
                    'menu_item_name': om.menu_item.name,
                    'quantity': om.quantity
                } for om in order_items
            ]

            data.append({
                'id': order.id,
                'user_id': order.user.id if order.user else None,
                'user_name': order.user.name if order.user else None,
                'datetime': order.datetime,
                'total_price': order.total_price,
                'status': order.status,
                'items': items_data
            })
        return JsonResponse(data, safe=False)


    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            items = data.get('items')

            if not user_id or not items:
                return JsonResponse({'error': 'Missing user_id or items'}, status=400)

            user = get_object_or_404(User, pk=user_id)

            order = Order.objects.create(
                user=user,
                status='pending',
                datetime=data.get('datetime'),
                total_price=0
            )

            total_price = 0

            for item in items:
                menu_item_id = item.get('menu_item_id')
                quantity = item.get('quantity', 1)

                if not menu_item_id or quantity <= 0:
                    continue

                menu_item = get_object_or_404(MenuItem, pk=menu_item_id)
                OrderMenu.objects.create(order=order, menu_item=menu_item, quantity=quantity)

                if menu_item.price:
                    total_price += menu_item.price * quantity

            order.total_price = total_price
            order.save()

            response_data = {
                'order_id': order.id,
                'user_id': order.user.id,
                'total_price': float(order.total_price),
                'status': order.status,
                'items': [
                    {'menu_item_id': item.get('menu_item_id'), 'quantity': item.get('quantity', 1)}
                    for item in items
                ]
            }

            return JsonResponse(response_data, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


# Update or delete an order
@csrf_exempt
#@permission_classes([OrderObjectAccess])
@permission_classes([AllowAny])
@require_http_methods(["GET", "PUT", "DELETE"])
def detalle_o_editar_o_eliminar_orden(request, orden_id):
    if request.method == 'GET':
        order = get_object_or_404(Order, pk=orden_id)
        order_items = OrderMenu.objects.filter(order=order).select_related('menu_item')
        items_data = [
            {
                'menu_item_id': om.menu_item.id,
                'menu_item_name': om.menu_item.name,
                'quantity': om.quantity
            } for om in order_items
        ]

        data = {
            'id': order.id,
            'user_id': order.user.id if order.user else None,
            'user_name': order.user.name if order.user else None,
            'datetime': order.datetime,
            'total_price': order.total_price,
            'status': order.status,
            'items': items_data
        }
        return JsonResponse(data)

    elif request.method == 'PUT':
        order = get_object_or_404(Order, pk=orden_id)
        data = json.loads(request.body)
        if 'status' in data:
            order.status = data['status']
        order.save()
        return JsonResponse({'id': order.id, 'status': order.status, 'user_id': order.user.id, 'total_price': order.total_price})

    elif request.method == 'DELETE':
        order = get_object_or_404(Order, pk=orden_id)
        order.delete()
        return JsonResponse({'message': 'Order deleted'})

#############################################################################################################################################################################################################################################################################################################################################################################################
# List or create order menu
@csrf_exempt
@require_http_methods(["GET", "POST"])
def listar_o_crear_order_menu(request):
    if request.method == 'GET':
        order_menus = OrderMenu.objects.select_related('order', 'menu_item').all()
        data = [
            {
                'id': om.id,
                'order_id': om.order.id if om.order else None,
                'menu_item_id': om.menu_item.id if om.menu_item else None,
                'menu_item_name': om.menu_item.name if om.menu_item else None,
                'quantity': om.quantity
            } for om in order_menus
        ]
        return JsonResponse(data, safe=False)

    elif request.method == 'POST':
        data = json.loads(request.body)
        try:
            order = get_object_or_404(Order, pk=data.get('order_id'))
            menu_item = get_object_or_404(MenuItem, pk=data.get('menu_item_id'))
            quantity = data.get('quantity', 1)  # Default to 1 if no quantity is provided

            order_menu = OrderMenu(order=order, menu_item=menu_item, quantity=quantity)
            order_menu.save()
            return JsonResponse({'id': order_menu.id, 'order_id': order_menu.order.id, 'menu_item_id': order_menu.menu_item.id, 'quantity': order_menu.quantity}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["DELETE", "GET"])
def detalle_o_eliminar_order_menu(request, orden_menu_id):
    if request.method == 'GET':
        om = get_object_or_404(OrderMenu, pk=orden_menu_id)
        data = {
            'id': om.id,
            'order_id': om.order.id if om.order else None,
            'menu_item_id': om.menu_item.id if om.menu_item else None,
            'menu_item_name': om.menu_item.name if om.menu_item else None,
            'quantity': om.quantity
        }
        return JsonResponse(data)

    elif request.method == 'DELETE':
        om = get_object_or_404(OrderMenu, pk=orden_menu_id)
        om.delete()
        return JsonResponse({'message': 'Order menu item deleted'})


#############################################################################################################################################################################################################################################################################################################################################################################################
@csrf_exempt
#@permission_classes([IsAdmin])
@permission_classes([AllowAny])
@require_http_methods(["GET"])
def listar_tablas(request):
    cursor = connection.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'app1%';")
    tables = cursor.fetchall()
    data = [{'table_name': table[0]} for table in tables]
    return JsonResponse(data, safe=False)
