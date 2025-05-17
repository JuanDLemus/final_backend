from django.db import models
from django.contrib.auth.hashers import (
    make_password,
    check_password,
    is_password_usable,
)

class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)  # Allow NULL and blank
    address = models.CharField(max_length=255, null=True, blank=True)  # Allow NULL and blank
    contact = models.CharField(max_length=20, null=True, blank=True)  # Allow NULL and blank
    buyer_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Allow NULL and blank
    password = models.CharField(max_length=255, null=True, blank=True)  # User password, allow NULL and blank
    
    def __str__(self):
        return self.name if self.name else "No Name"

    def set_password(self, raw_password):
        """Hashes and sets the password."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Checks if the provided password matches the stored hash."""
        return check_password(raw_password, self.password)

    def set_unusable_password(self):
        """Marks this user as having no password."""
        self.password = make_password(None)

    def has_usable_password(self):
        """Returns False if set_unusable_password was called."""
        return is_password_usable(self.password)

class Employee(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    secret_password = models.CharField(max_length=255, default="default_password", null=True, blank=True)
    image = models.ImageField(upload_to='employee_images/', null=True, blank=True)
    role = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.name if self.user else 'No User'} - {self.role if self.role else 'No Role'}"

    def set_secret_password(self, raw_password):
        self.secret_password = make_password(raw_password)

    def check_secret_password(self, raw_password):
        return check_password(raw_password, self.secret_password)

    def set_unusable_secret_password(self):
        self.secret_password = make_password(None)

    def has_usable_secret_password(self):
        return is_password_usable(self.secret_password)
    
class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('burger', 'Burger'),
        ('dessert', 'Dessert'),
        ('drink', 'Drink'),
        ('fast', 'Fast Food')
    ]
    
    id = models.AutoField(primary_key=True)
    image_link = models.URLField(max_length=255, null=True, blank=True)  # Allow NULL and blank
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    ingredients = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    awareness = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, null=True, blank=True)
    calories = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name if self.name else "No Name"

class Order(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Allow NULL and blank
    datetime = models.DateTimeField(null=True, blank=True)  # Allow NULL and blank
    total_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # Allow NULL and blank
    status = models.CharField(max_length=20, choices=[('delivered', 'Delivered'), ('pending', 'Pending')], null=True, blank=True)  # Allow NULL and blank

    def __str__(self):
        return f"Order {self.id} for {self.user.name if self.user else 'No User'}"

class OrderMenu(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)  # Allow NULL and blank
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True)  # Allow NULL and blank
    quantity = models.PositiveIntegerField(null=True, blank=True)  # Allow NULL and blank

    class Meta:
        unique_together = ('order', 'menu_item')

    def __str__(self):
        return f"Order {self.order.id if self.order else 'No Order'} - Item {self.menu_item.name if self.menu_item else 'No Item'} x{self.quantity if self.quantity else 'No Quantity'}"
