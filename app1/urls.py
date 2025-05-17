from django.contrib import admin
from django.urls import path, re_path
from . import views

urlpatterns = [
    # User routes
    path('usuarios/', views.listar_o_crear_usuario, name='listar_o_crear_usuario'),
    path('usuarios/<int:usuario_id>/', views.detalle_o_editar_o_eliminar_usuario, name='detalle_o_editar_o_eliminar_usuario'),

    # Menu routes
    path('menu/', views.listar_o_crear_menu_item, name='listar_o_crear_menu_item'),
    path('menu/<int:menu_id>/', views.detalle_o_editar_o_eliminar_menu_item, name='detalle_o_editar_o_eliminar_menu_item'),

    # Order routes
    path('ordenes/', views.listar_o_crear_orden, name='listar_o_crear_orden'),
    path('ordenes/<int:orden_id>/', views.detalle_o_editar_o_eliminar_orden, name='detalle_o_editar_o_eliminar_orden'),

    # OrderMenu routes
    path('ordenmenu/', views.listar_o_crear_order_menu, name='listar_o_crear_order_menu'),
    path('ordenmenu/<int:orden_menu_id>/', views.detalle_o_eliminar_order_menu, name='detalle_o_editar_o_eliminar_order_menu'),
    
    # Employee routes
    path('empleados/', views.listar_o_crear_empleado, name='listar_o_crear_empleado'),
    path('empleados/<int:empleado_id>/', views.detalle_o_editar_o_eliminar_empleado, name='detalle_o_editar_o_eliminar_empleado'),

    # Endpoint to list all tables in the database
    path('tablas/', views.listar_tablas, name='listar_tablas'),

    re_path('login/', views.login),
    re_path('register/', views.register),
    re_path('profile/', views.profile),
]
