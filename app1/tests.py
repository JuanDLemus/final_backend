from django.test import TestCase

# Create your tests here.
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import User, MenuItem, Order, Employee

class RestaurantAPITest(APITestCase):

    def setUp(self):
        # Create a user and a menu item
        self.user = User.objects.create(username="john_doe", email="john@example.com")
        self.menu_item = MenuItem.objects.create(name="Cheeseburger", description="A delicious cheeseburger", price=5.99)
        self.order_data = {
            "user": self.user.id,
            "status": "in_progress",
            "order_menu_items": [{"menu_item": self.menu_item.id, "quantity": 2}]
        }

    def test_create_user(self):
        url = reverse('user-list-create')
        data = {
            "username": "jane_doe",
            "email": "jane@example.com"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'jane_doe')

    def test_list_users(self):
        url = reverse('user-list-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only one user created in setUp

    def test_create_order(self):
        url = reverse('order-list-create')
        response = self.client.post(url, self.order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'in_progress')
        self.assertEqual(len(response.data['order_menu_items']), 1)

    def test_update_order_status(self):
        order = Order.objects.create(user=self.user, status='in_progress')
        url = reverse('update-order-status', kwargs={'pk': order.id})
        data = {"status": "delivered"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'delivered')
