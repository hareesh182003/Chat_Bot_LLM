from rest_framework import serializers
from app.models import *
import secrets
import string


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password", "email", "user_category", "must_change_password"]
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            "must_change_password": {"read_only": True},  # ✅ prevent direct edits
        }

    def create(self, validated_data):
        request = self.context.get("request")

        # ✅ Editors can only create customers (ignore whatever is passed)
        if request and request.user.user_category == "editor":
            validated_data["user_category"] = "customer"

        password = validated_data.pop("password", None)
        if not password:
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(10))

        user = User(
            username=validated_data["username"],
            email=validated_data.get("email"),
            user_category=validated_data.get("user_category", "customer"),  # forced above
            must_change_password=True
        )
        user.set_password(password)
        user.save()
        self._generated_password = password
        return user



    def update(self, instance, validated_data):
        request = self.context.get("request")

        # Permission checks (unchanged)
        if request and request.user.user_category == "editor":
            if instance.user_category in ["admin", "editor"]:
                raise PermissionError("Editors can only update customers.")
            validated_data.pop("user_category", None)

        if request and request.user.user_category == "customer":
            if instance.id != request.user.id:
                raise PermissionError("Customers can only update their own profile.")
            validated_data.pop("user_category", None)

        # ✅ NEW: Auto-allow password change if must_change_password is True (forced reset)
        allow_password_change = self.context.get("allow_password_change", False)
        if instance.must_change_password:
            allow_password_change = True  # Override for first-time reset

        # Only discard password if not allowed
        if not allow_password_change:
            validated_data.pop("password", None)

        # Handle everything except password first
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Handle password safely
        if password:
            instance.set_password(password)  # Hashes the password
            instance.must_change_password = False  # Reset the flag

        instance.save()
        return instance




class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class ShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipping
        fields = '__all__'
