from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .serializers import *
from app.models import *
from app.utils.llm_agent import call_llm, execute_action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny
from app.permissions import MustChangePasswordPermission
from django.shortcuts import render

def chatbot_ui(request):
    return render(request, "chat_bot.html")

class RegisterView(APIView):
    permission_classes = [AllowAny]   # ✅ anyone can access

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if serializer.is_valid():
            user = serializer.save()
            response_data = serializer.data
            if hasattr(serializer, "_generated_password"):
                response_data["temporary_password"] = serializer._generated_password
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class BaseCRUDView(APIView):
    model = None
    serializer_class = None
    lookup_field = "id"
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, MustChangePasswordPermission]

    def get_queryset(self):
        return self.model.objects.all()

    def get_object(self, obj_id):
        return get_object_or_404(self.model, id=obj_id)

    def get(self, request, obj_id=None):
        if obj_id:
            instance = self.get_object(obj_id)
            serializer = self.serializer_class(instance, context={"request": request})
        else:
            queryset = self.get_queryset()
            serializer = self.serializer_class(queryset, many=True, context={"request": request})
        return Response(serializer.data)
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if serializer.is_valid():
            user = serializer.save()
            response_data = serializer.data
            if hasattr(serializer, "_generated_password"):
                response_data["temporary_password"] = serializer._generated_password
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, obj_id=None):
        if not obj_id:
            return Response({"error": "ID required"}, status=status.HTTP_400_BAD_REQUEST)
        instance = self.get_object(obj_id)
        serializer = self.serializer_class(instance, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, obj_id=None):
        if not obj_id:
            return Response({"error": "ID required"}, status=status.HTTP_400_BAD_REQUEST)
        instance = self.get_object(obj_id)
        serializer = self.serializer_class(instance, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, obj_id=None):
        if not obj_id:
            return Response({"error": "ID required"}, status=status.HTTP_400_BAD_REQUEST)
        instance = self.get_object(obj_id)
        instance.delete()
        return Response({"deleted": True}, status=status.HTTP_204_NO_CONTENT)







class UserAPIView(BaseCRUDView):
    model = User
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.user_category == "customer":
            return self.model.objects.filter(id=user.id)  # ✅ only self
        return super().get_queryset()

class CategoryAPIView(BaseCRUDView):
    model = Category
    serializer_class = CategorySerializer

class ProductAPIView(BaseCRUDView):
    model = Product
    serializer_class = ProductSerializer

class SupplierAPIView(BaseCRUDView):
    model = Supplier
    serializer_class = SupplierSerializer

class InventoryAPIView(BaseCRUDView):
    model = Inventory
    serializer_class = InventorySerializer

class OrderAPIView(BaseCRUDView):
    model = Order
    serializer_class = OrderSerializer

class OrderItemAPIView(BaseCRUDView):
    model = OrderItem
    serializer_class = OrderItemSerializer

class ReviewAPIView(BaseCRUDView):
    model = Review
    serializer_class = ReviewSerializer

class PaymentAPIView(BaseCRUDView):
    model = Payment
    serializer_class = PaymentSerializer

class ShippingAPIView(BaseCRUDView):
    model = Shipping
    serializer_class = ShippingSerializer


# ---------------------------
# LLM Agent View (RBAC-aware)
# ---------------------------
class LLMActionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, MustChangePasswordPermission]

    def post(self, request):
        prompt = request.data.get("prompt")
        if not prompt:
            return Response({"error": "Prompt required"}, status=400)

        # Actor = logged-in user role
        user_role = getattr(request.user, "user_category", "customer")

        # Get the actual Bearer token from request headers
        auth_header = request.headers.get("Authorization", "")
        jwt_token = auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else None

        action_json = call_llm(prompt)
        result = execute_action(action_json, user_role=user_role, jwt_token=jwt_token,  current_user=request.user)

        return Response({
            "user": request.user.username,
            "role": user_role,
            "action": action_json,
            "result": result
        })



class CurrentUserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, MustChangePasswordPermission]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(
            request.user, 
            data=request.data, 
            partial=True, 
            context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

