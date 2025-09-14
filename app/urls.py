from django.urls import path
from .views import (
    UserAPIView, CategoryAPIView, ProductAPIView,
    SupplierAPIView, InventoryAPIView, OrderAPIView,
    OrderItemAPIView, ReviewAPIView, PaymentAPIView,
    ShippingAPIView, LLMActionView, RegisterView, CurrentUserView, chatbot_ui
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Map view classes to their route names
crud_routes = {
    "users": UserAPIView,
    "categories": CategoryAPIView,
    "products": ProductAPIView,
    "suppliers": SupplierAPIView,
    "inventories": InventoryAPIView,
    "orders": OrderAPIView,
    "orderitems": OrderItemAPIView,
    "reviews": ReviewAPIView,
    "payments": PaymentAPIView,
    "shippings": ShippingAPIView,
}

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("llm-action/", LLMActionView.as_view(), name="llm-action"),
    path("token/", TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("token/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("chatbot/", chatbot_ui, name="chatbot-ui"),

]

# Auto-generate CRUD routes for each model
for route, view in crud_routes.items():
    urlpatterns += [
        path(f"{route}/", view.as_view(), name=f"{route}-list"),
        path(f"{route}/<int:obj_id>/", view.as_view(), name=f"{route}-detail"),
    ]
