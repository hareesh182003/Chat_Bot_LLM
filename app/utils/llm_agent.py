from django.apps import apps
from openai import OpenAI
from django.conf import settings
import requests
import json
import inflection
from app.utils.rbac import check_rbac
from django.apps import apps

client = OpenAI(api_key=settings.PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")

DJANGO_API_BASE = "http://127.0.0.1:8000/api/"


def model_to_endpoint(model):
    """
    Convert Django model class name into API endpoint format.
    Example:
        User -> /users/
        Category -> /categories/
        Person -> /people/
    """
    model_name = model.__name__.lower()
    plural = inflection.pluralize(model_name)
    return f"/{plural}/"



def get_api_schema():
    schema = {}
    for model in apps.get_models():
        app_label = model._meta.app_label
        if app_label in ["admin", "auth", "contenttypes", "sessions"]:
            continue  # skip Django system models

        endpoint = model_to_endpoint(model).strip("/")
        fields_info = []
        for f in model._meta.get_fields():
            if f.concrete and not f.auto_created:
                fields_info.append({
                    "name": f.name,
                    "required": not f.blank and not f.null and not f.primary_key
                })
        schema[endpoint] = fields_info
    return schema




def build_system_message():
    API_SCHEMA = get_api_schema()

    msg = "You are a database agent.\n"
    msg += "Convert user requests into valid JSON instructions.\n"
    msg += "Available APIs:\n"

    for model, fields in API_SCHEMA.items():
        required_fields = [f['name'] for f in fields if f['required'] and f['name'] != "id"]
        optional_fields = [f['name'] for f in fields if not f['required'] and f['name'] != "id"]

        msg += f"""
        {model.upper()}:
        - GET /{model}/
        - GET /{model}/<id>/
        - POST /{model}/ (required: {required_fields}, optional: {optional_fields})
        - PUT /{model}/<id>/ (all required fields must be included, optional fields can also be included)
        - PATCH /{model}/<id>/ (use for updating only some fields, both required and optional allowed)
        - DELETE /{model}/<id>/
        """
    msg += """
    SPECIAL ENDPOINTS:
    - GET /me/ (returns the currently logged-in user)
    """
    msg += """
    SPECIAL ENDPOINTS:
    - GET /all-tables/ (returns the list of table names; admin only)
    """
    msg += """
    SPECIAL ENDPOINTS:
    - POST /register/ (fields: username, password, email)
    - POST /token/ (fields: username, password)
    - POST /token/refresh/ (fields: refresh)
    - GET /me/ (returns the current user)
    - PATCH /me/ (update your own details, e.g., change password)
    """

    msg += """
    Return ONLY JSON in this format:
    {"method": "GET|POST|PUT|PATCH|DELETE", "endpoint": "/table_name/1/", "data": {...} }

    Rules:
    - Use PATCH if the user request mentions updating a single field or a few fields.
    - Use PUT if the user request mentions replacing the full record.
    - Ensure required fields are always present for POST and PUT.
    - If the user asks to "show all tables" or "list all tables", return the endpoint "/all-tables/" with method "GET".

    Example:
    Input: "Show all tables in the database"
    Output: {"method": "GET", "endpoint": "/all-tables/"}
    """
    return msg


def call_llm(prompt):
    system_message = build_system_message()
    response = client.chat.completions.create(
        model="sonar",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


def execute_action(action_json, user_role="customer", jwt_token=None, current_user=None, prompt=None):
    try:
        # If caller provided the original prompt, detect show-all-tables intent and override
        if prompt:
            low = prompt.lower()
            intent_show_tables = any(kw in low for kw in ["show all tables", "list all tables", "show tables", "all tables"]) 
            if intent_show_tables:
                # Only admins are allowed to list all tables
                if getattr(current_user, 'user_category', None) != 'admin':
                    return {"error": "Admin access required to list all tables."}
                action = {"method": "GET", "endpoint": "/all-tables/"}
            else:
                # parse LLM output if not overridden
                action = json.loads(action_json) if isinstance(action_json, str) else action_json
        else:
            action = json.loads(action_json) if isinstance(action_json, str) else action_json

        # Basic validation of action
        if not isinstance(action, dict) or 'method' not in action or 'endpoint' not in action:
            return {"error": "Invalid action format returned by LLM"}

        # RBAC check before calling Django API
        check_rbac(user_role, action, current_user=current_user)

        url = DJANGO_API_BASE.rstrip("/") + "/" + action["endpoint"].lstrip("/")

        headers = {}
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"

        method = action["method"].upper()
        if method == "GET":
            res = requests.get(url, headers=headers)
        elif method == "POST":
            res = requests.post(url, json=action.get("data", {}), headers=headers)
        elif method == "PUT":
            res = requests.put(url, json=action.get("data", {}), headers=headers)
        elif method == "PATCH":
            res = requests.patch(url, json=action.get("data", {}), headers=headers)
        elif method == "DELETE":
            res = requests.delete(url, headers=headers)
        else:
            return {"error": "Invalid method"}

        # Try to return JSON, fall back to text/status when necessary
        try:
            return res.json() if res.content else {"status": res.status_code}
        except ValueError:
            return {"status": res.status_code, "text": res.text}
    except PermissionError as pe:
        return {"error": str(pe)}
    except Exception as e:
        return {"error": str(e)}


