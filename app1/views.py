import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import connection
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import authenticate
from .models import User, MenuItem, Order, Employee, OrderMenu
from .serializers import UserSerializer
from .permissions import IsRegistration, IsSelf, IsMenu, IsAdmin, IsOrder

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
@permission_classes([IsAuthenticated])
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
@permission_classes([IsRegistration])
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
@permission_classes([IsSelf])
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
# List or create employee
@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def listar_o_crear_empleado(request):
    if request.method == 'GET':
        empleados = Employee.objects.select_related('user').all()
        data = [
            {
                'id': e.id,
                'user_id': e.user.id,
                'user_name': e.user.name,
                'image': request.build_absolute_uri(e.image.url) if e.image else None,
                'role': e.role,
                'description': e.description
            }
            for e in empleados
        ]
        return Response(data)

    # POST path (only reachable if IsEmployee passes)
    payload = request.data
    password = payload.get('password')
    if not password:
        return Response({"error": "Password is required"}, status=status.HTTP_400_BAD_REQUEST)

    user_data = {
        'name':        payload.get('name'),
        'address':     payload.get('address'),
        'contact':     payload.get('contact'),
        'buyer_score': payload.get('buyer_score', 0),
        'password':    password
    }
    user_ser = UserSerializer(data=user_data)
    user_ser.is_valid(raise_exception=True)
    user = user_ser.save()
    token, _ = Token.objects.get_or_create(user=user)

    try:
        empleado = Employee.objects.create(
            user        = user,
            image       = payload.get('image'),
            role        = payload.get('role'),
            description = payload.get('description')
        )
        return Response({
            'token':       token.key,
            'employee_id': empleado.id,
            'user_id':     user.id,
            'name':        user.name,
            'role':        empleado.role
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        user.delete()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Update or delete employee
@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsSelf])
def detalle_o_editar_o_eliminar_empleado(request, empleado_id):
    if request.method == 'GET':
        empleado = get_object_or_404(Employee, pk=empleado_id)
        data = {
            'id': empleado.id,
            'user_id': empleado.user.id if empleado.user else None,
            'user_name': empleado.user.name if empleado.user else None,
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
## List or create menu item
@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsMenu])
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

@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsMenu])
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
# List or create order
@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsOrder])
def listar_o_crear_orden(request):
    user = request.user

    if request.method == 'GET':
        if hasattr(user, 'employee') or user.is_staff:
            orders = Order.objects.select_related('user').all()
        else:
            orders = Order.objects.filter(user=user).select_related('user')

        data = []
        for order in orders:
            order_items = OrderMenu.objects.filter(order=order).select_related('menu_item')
            items_data = [
                {
                    'menu_item_id': om.menu_item.id,
                    'menu_item_name': om.menu_item.name,
                    'menu_item_price': float(om.menu_item.price),
                    'quantity': om.quantity,
                    'subtotal': float(om.menu_item.price * om.quantity)
                } for om in order_items
            ]

            data.append({
                'id': order.id,
                'user_id': order.user.id if order.user else None,
                'user_name': order.user.name if order.user else None,
                'datetime': order.datetime,
                'total_price': float(order.total_price),
                'status': order.status,
                'items': items_data
            })

        return JsonResponse(data, safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items')

            if not items:
                return JsonResponse({'error': 'Missing items'}, status=400)

            user_id = data.get('user_id')
            if user_id and user.is_staff:
                user_obj = get_object_or_404(User, pk=user_id)
            else:
                user_obj = user

            order = Order.objects.create(
                user=user_obj,
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
@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsOrder])
def detalle_o_editar_o_eliminar_orden(request, orden_id):
    user = request.user
    order = get_object_or_404(Order, pk=orden_id)

    if request.method == 'GET':
        if order.user != user and not hasattr(user, 'employee') and not user.is_staff:
            return JsonResponse({'error': 'Forbidden'}, status=403)

        order_items = OrderMenu.objects.filter(order=order).select_related('menu_item')
        items_data = [
            {
                'menu_item_id': om.menu_item.id,
                'menu_item_name': om.menu_item.name,
                'menu_item_price': float(om.menu_item.price),
                'quantity': om.quantity,
                'subtotal': float(om.menu_item.price * om.quantity)
            } for om in order_items
        ]

        data = {
            'id': order.id,
            'user_id': order.user.id if order.user else None,
            'user_name': order.user.name if order.user else None,
            'datetime': order.datetime,
            'total_price': float(order.total_price),
            'status': order.status,
            'items': items_data
        }
        return JsonResponse(data)

    elif request.method == 'PUT':
        if not hasattr(user, 'employee') and not user.is_staff:
            return JsonResponse({'error': 'Only employees can update orders'}, status=403)

        data = json.loads(request.body)
        if 'status' in data:
            order.status = data['status']
        order.save()

        return JsonResponse({
            'id': order.id,
            'status': order.status,
            'user_id': order.user.id,
            'total_price': float(order.total_price)
        })

    elif request.method == 'DELETE':
        if not user.is_staff:
            return JsonResponse({'error': 'Only admins can delete orders'}, status=403)

        order.delete()
        return JsonResponse({'message': 'Order deleted'})


#############################################################################################################################################################################################################################################################################################################################################################################################
# List or create order menu
@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
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

@api_view(["DELETE", "GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
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
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def listar_tablas(request):
    cursor = connection.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'app1%';")
    tables = cursor.fetchall()
    data = [{'table_name': table[0]} for table in tables]
    return JsonResponse(data, safe=False)
