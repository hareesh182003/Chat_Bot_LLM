
from app.utils.rbac_schema import RBAC_POLICIES


def check_rbac(user_role, action, current_user=None):
    method = action.get("method")
    endpoint_parts = action.get("endpoint").strip("/").split("/")
    endpoint = endpoint_parts[0]  # e.g., "users"
    target_id = endpoint_parts[1] if len(endpoint_parts) > 1 else None

    allowed_methods = RBAC_POLICIES.get(user_role, {}).get(endpoint, [])
    if method not in allowed_methods:
        raise PermissionError(f"Role '{user_role}' not allowed to perform {method} on {endpoint}")

    if endpoint == "users":
        # ❌ Editors cannot delete users
        if user_role == "editor" and method == "DELETE":
            raise PermissionError("Editors cannot delete users.")

        # ❌ Editors can update only customers
        if user_role == "editor" and method in ["PATCH", "PUT"]:
            if not current_user or current_user.user_category != "customer":
                raise PermissionError("Editors can only update customers.")

        # ❌ Customers can only update their own profile
        if user_role == "customer" and method in ["PATCH", "PUT"]:
            if not current_user:
                raise PermissionError("Customer identity not provided.")
            if not target_id or str(current_user.id) != str(target_id):
                raise PermissionError("Customers can only update their own profile.")
