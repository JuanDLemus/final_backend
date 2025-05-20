from django.db import models
from django.db.models import Max
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class NextIDMixin(models.Model):
    id = models.PositiveIntegerField(primary_key=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self._state.adding and self.id is None:
            max_id = self.__class__.objects.aggregate(max_id=Max('id'))['max_id'] or 0
            self.id = max_id + 1
        super().save(*args, **kwargs)

class CustomUserManager(BaseUserManager):
    def create_user(self, name, password=None, **extra_fields):
        if not name:
            raise ValueError('El nombre es obligatorio')
        user = self.model(name=name, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(name, password, **extra_fields)

# ← Here we mix in NextIDMixin!
class User(NextIDMixin, AbstractBaseUser, PermissionsMixin):
    name        = models.CharField(max_length=255, unique=True)
    address     = models.CharField(max_length=255, null=True, blank=True)
    contact     = models.CharField(max_length=20,  null=True, blank=True)
    buyer_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)

    USERNAME_FIELD  = 'name'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.name

class Employee(NextIDMixin):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='employee_images/', null=True, blank=True)
    role = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.name if self.user else 'No User'} - {self.role if self.role else 'No Role'}"

class MenuItem(NextIDMixin):
    CATEGORY_CHOICES = [
        ('burger', 'Burger'),
        ('dessert', 'Dessert'),
        ('drink', 'Drink'),
        ('fast', 'Fast Food')
    ]

    image_link = models.URLField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    ingredients = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    awareness = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, null=True, blank=True)
    calories = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name if self.name else "No Name"

class Order(NextIDMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    datetime = models.DateTimeField(null=True, blank=True)
    total_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('delivered', 'Delivered'), ('pending', 'Pending')], null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} for {self.user.name if self.user else 'No User'}"

class OrderMenu(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('order', 'menu_item')

    def __str__(self):
        return f"Order {self.order.id if self.order else 'No Order'} - Item {self.menu_item.name if self.menu_item else 'No Item'} x{self.quantity if self.quantity else 'No Quantity'}"
