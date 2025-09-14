# Django ORM models for e-commerce context
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # AbstractUser already includes: username, password, email, first_name, last_name
	user_category = models.CharField(
		max_length=50,
		choices=[("admin", "Admin"), ("editor", "Editor"), ("customer", "Customer")],
		default="customer"
	)
	must_change_password = models.BooleanField(default=True)
	def __str__(self):
		return self.username

class Category(models.Model):
	name = models.CharField(max_length=100)

	def __str__(self):
		return self.name

class Product(models.Model):
	def clean(self):
		if self.price is not None and self.price < 0:
			raise ValidationError({'price': 'Price cannot be negative.'})
		if not self.name:
			raise ValidationError({'name': 'Product name is required.'})
	name = models.CharField(max_length=100)
	price = models.FloatField()
	category = models.ForeignKey(Category, on_delete=models.CASCADE)

	def __str__(self):
		return self.name

class Supplier(models.Model):
	def clean(self):
		if not self.name:
			raise ValidationError({'name': 'Supplier name is required.'})
	name = models.CharField(max_length=100)
	contact_info = models.TextField()

	def __str__(self):
		return self.name

class Inventory(models.Model):
	def clean(self):
		if self.quantity is not None and self.quantity < 0:
			raise ValidationError({'quantity': 'Quantity cannot be negative.'})
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
	quantity = models.IntegerField()

	def __str__(self):
		return self.product.name
	
class Order(models.Model):
	def clean(self):
		if not self.user:
			raise ValidationError({'user': 'User is required for an order.'})
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	order_date = models.DateTimeField()

	def __str__(self):
		return self.user.username


class OrderItem(models.Model):
    def clean(self):
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be greater than zero.'})
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return self.product.name


class Review(models.Model):
	def clean(self):
		if self.rating is not None and (self.rating < 1 or self.rating > 5):
			raise ValidationError({'rating': 'Rating must be between 1 and 5.'})
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	rating = models.IntegerField()
	comment = models.TextField()

	def __str__(self):
		return self.product.name

class Payment(models.Model):
	def clean(self):
		if self.amount is not None and self.amount < 0:
			raise ValidationError({'amount': 'Amount cannot be negative.'})
	order = models.ForeignKey(Order, on_delete=models.CASCADE)
	amount = models.FloatField()
	payment_date = models.DateTimeField()

	def __str__(self):
		return self.order.user.username
	
class Shipping(models.Model):
	def clean(self):
		if not self.address:
			raise ValidationError({'address': 'Shipping address is required.'})
	order = models.ForeignKey(Order, on_delete=models.CASCADE)
	address = models.TextField()
	shipped_date = models.DateTimeField()

	def __str__(self):
		return self.order.user.username
