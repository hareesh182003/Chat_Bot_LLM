# app/utils/rbac.py
RBAC_POLICIES = {
    "admin": {
        "users": ["GET", "POST", "PUT", "PATCH", "DELETE"],
        "categories": ["GET", "POST", "PUT", "PATCH", "DELETE"],
        "products": ["GET", "POST", "PUT", "PATCH", "DELETE"],
        "suppliers": ["GET", "POST", "PUT", "PATCH", "DELETE"],
        "inventories": ["GET", "POST", "PUT", "PATCH", "DELETE"],
        "orders": ["GET", "POST", "PUT", "PATCH", "DELETE"],
        "orderitems": ["GET", "POST", "PUT", "PATCH", "DELETE"],
        "reviews": ["GET", "POST", "PUT", "PATCH", "DELETE"],
        "payments": ["GET", "POST", "PUT", "PATCH"],
        "shippings": ["GET", "POST", "PUT", "PATCH"],
        "tokens": ["GET", "POST", "DELETE"],
        "me": ["GET", "PATCH"],
    },
    "customer": {
        "users": ["GET", "PATCH"],  # profile only
        "products": ["GET"],
        "orders": ["GET", "POST"],
        "orderitems": ["GET"],
        "reviews": ["GET", "POST"],
        "payments": ["GET", "POST"],
        "shippings": ["GET"],
        "me": ["GET"],
    },
    "editor": {
    "users": ["GET", "POST", "PUT", "PATCH"],  # ✅ but limited by logic
    "orders": ["GET", "PATCH"],
    "shippings": ["GET", "POST", "PATCH"],
    "inventories": ["GET", "PATCH"],
    "me": ["GET", "PATCH"],
    }

}
