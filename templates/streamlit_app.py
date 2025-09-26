import streamlit as st
import requests
import json
import pandas as pd
from typing import Optional, List, Dict

API_BASE = "http://127.0.0.1:8000/api"

st.set_page_config(page_title="Chat Bot LLM - Streamlit", layout="centered")

# ------------------ Helpers ------------------ #
def api_post(path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.post(API_BASE + path, json=data or {}, headers=headers)

def api_patch(path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.patch(API_BASE + path, json=data or {}, headers=headers)

def api_get(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.get(API_BASE + path, headers=headers)

def refresh_token():
    """Try to refresh the access token."""
    refresh = st.session_state.get("refresh_token")
    if not refresh:
        return False
    res = api_post("/token/refresh/", {"refresh": refresh})
    if res.ok:
        data = res.json()
        st.session_state["access_token"] = data.get("access")
        return True
    return False

def call_llm(prompt):
    """Call LLM with automatic token refresh on 401/403."""
    token = st.session_state.get("access_token")
    res = api_post("/llm-action/", {"prompt": prompt}, token=token)
    if res.status_code in (401, 403):
        if refresh_token():
            token = st.session_state.get("access_token")
            res = api_post("/llm-action/", {"prompt": prompt}, token=token)
    return res

# ------------------ UI ------------------ #
st.title("Chat Bot LLM - Streamlit UI")

# ------------------ Login ------------------ #
if "access_token" not in st.session_state and "require_password_change" not in st.session_state:
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        res = api_post("/token/", {"username": username, "password": password})
        if res.ok:
            data = res.json()
            access = data.get("access")
            refresh = data.get("refresh")

            # 🔹 Fetch user profile after login
            res_me = api_get("/me/", token=access)
            if res_me.ok:
                user_info = res_me.json()
                if user_info.get("must_change_password"):
                    # Force password reset
                    st.session_state["require_password_change"] = True
                    st.session_state["temp_username"] = username
                    st.session_state["temp_password"] = password
                    st.session_state["temp_access"] = access
                    st.session_state["temp_refresh"] = refresh
                    st.warning("You must change your default password before continuing.")
                    st.rerun()
                else:
                    # Normal login
                    st.session_state["access_token"] = access
                    st.session_state["refresh_token"] = refresh
                    st.session_state["chat_history"] = []
                    st.success("Logged in successfully")
                    st.rerun()
            else:
                st.error("Failed to fetch user info after login")
        else:
            st.error("Login failed")

# ------------------ First Login Password Reset ------------------ #
# elif st.session_state.get("require_password_change"):
#     st.header("Reset Default Password")
#     new_password = st.text_input("New Password", type="password")
#     confirm_password = st.text_input("Confirm Password", type="password")

#     if st.button("Change Password"):
#         if not new_password or not confirm_password:
#             st.error("Please fill in both fields.")
#         elif new_password != confirm_password:
#             st.error("Passwords do not match.")
#         else:
#             # 🔹 Use temp access token to patch password
#             token = st.session_state.get("temp_access")
#             res_patch = api_patch("/me/", {"password": new_password}, token=token)

#             if res_patch.ok:
#                 # ✅ Re-login with new password to confirm must_change_password = False
#                 username = st.session_state.get("temp_username")
#                 res_login = api_post("/token/", {"username": username, "password": new_password})
#                 if res_login.ok:
#                     tokens = res_login.json()
#                     access = tokens.get("access")
#                     refresh = tokens.get("refresh")

#                     # Fetch /me/ again
#                     res_me = api_get("/me/", token=access)
#                     if res_me.ok:
#                         user_info = res_me.json()
#                         if not user_info.get("must_change_password"):
#                             st.success("Password updated successfully. You are now logged in.")
#                             st.session_state.clear()
#                             st.session_state["access_token"] = access
#                             st.session_state["refresh_token"] = refresh
#                             st.session_state["chat_history"] = []
#                             st.rerun()
#                         else:
#                             st.error("Password updated but system still requires reset. Contact admin.")
#                     else:
#                         st.error("Password updated but failed to fetch profile. Try logging in again.")
#                 else:
#                     error_msg = res_patch.text if res_patch.text else "Unknown error"
#                     st.error(f"Failed to update password: {res_patch.status_code} - {error_msg}")
#                 st.error("Failed to update password.")


elif st.session_state.get("require_password_change"):
    st.header("Reset Default Password")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Change Password"):
        if not new_password or not confirm_password:
            st.error("Please fill in both fields.")
        elif new_password != confirm_password:
            st.error("Passwords do not match.")
        else:
            # 🔹 Use temp access token to patch password
            token = st.session_state.get("temp_access")
            res_patch = api_patch("/me/", {"password": new_password}, token=token)

            if res_patch.ok:
                # ✅ Re-login with new password to confirm must_change_password = False
                username = st.session_state.get("temp_username")
                res_login = api_post("/token/", {"username": username, "password": new_password})
                if res_login.ok:
                    tokens = res_login.json()
                    access = tokens.get("access")
                    refresh = tokens.get("refresh")

                    # Fetch /me/ again
                    res_me = api_get("/me/", token=access)
                    if res_me.ok:
                        user_info = res_me.json()
                        if not user_info.get("must_change_password"):
                            st.success("Password updated successfully. You are now logged in.")
                            st.session_state.clear()
                            st.session_state["access_token"] = access
                            st.session_state["refresh_token"] = refresh
                            st.session_state["chat_history"] = []
                            st.rerun()
                        else:
                            st.error("Password updated but system still requires reset. Contact admin.")
                    else:
                        st.error(f"Password updated but failed to fetch profile: {res_me.status_code}")
                else:
                    st.error(f"Password updated but failed to re-login: {res_login.status_code} {res_login.text}")
            else:
                st.error(f"Failed to update password: {res_patch.status_code} {res_patch.text}")



# ------------------ Main App ------------------ #
else:
    # Sidebar with theme toggle
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4712/4712100.png", width=80)  
    st.sidebar.markdown("### 🤖 Chat Bot LLM")
    st.sidebar.divider()

    # Theme toggle
    theme = st.sidebar.radio("🌗 Theme", ["Light", "Dark"], index=0)

    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    # Apply theme CSS
    if theme == "Dark":
        st.markdown("""
            <style>
            body, .stApp { background-color: #1e1e1e !important; color: #ffffff !important; }
            .user-bubble { background-color: #DCF8C6; color: #000000; }
            .bot-bubble { background-color: #2c2c2c; color: #ffffff; }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            body, .stApp { background-color: #ffffff !important; color: #000000 !important; }
            .user-bubble { background-color: #DCF8C6; color: #000000; }
            .bot-bubble { background-color: #F1F0F0; color: #000000; }
            </style>
        """, unsafe_allow_html=True)

    st.header("💬 Chat with LLM")

    # Chat history display
    for entry in st.session_state["chat_history"]:
        role = entry["role"]
        content = entry.get("content", "")
        table_data = entry.get("table_data", None)

        if role == "user":
            st.markdown(
                f"""
                <div class="user-bubble" style="padding:10px 15px; border-radius:15px; margin:8px 0; 
                max-width:70%; float:right; clear:both;">
                🧑 <b>You</b><br>{content}
                </div>
                """, unsafe_allow_html=True)

        else:  # bot
            st.markdown(
                f"""
                <div class="bot-bubble" style="padding:10px 15px; border-radius:15px; margin:8px 0; 
                max-width:70%; float:left; clear:both;">
                🤖 <b>Bot</b><br>{content}
                </div>
                """, unsafe_allow_html=True)

            if table_data and isinstance(table_data, list) and len(table_data) > 0:
                df = pd.DataFrame(table_data)

                if len(df) == 1:
                    record = df.iloc[0].to_dict()
                    st.markdown("### 📇 User Details")

                    # 🔹 Card style display for single user
                    for k, v in record.items():
                        st.markdown(
                            f"""
                            <div style="
                                background-color:#1e1e1e;
                                padding:12px;
                                border-radius:10px;
                                margin-bottom:8px;
                                border:1px solid #444;
                            ">
                                <strong style="color:#4CAF50;">{k.capitalize()}</strong>: 
                                <span style="color:#f5f5f5;">{v}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    st.dataframe(df, use_container_width=True)

    # Input box (chat-style)
    if prompt := st.chat_input("Type your message..."):
        st.session_state["chat_history"].append({
            "role": "user",
            "content": prompt,
            "table_data": None
        })

        res = call_llm(prompt)
        if res.ok:
            try:
                data = res.json()
                summary = f"👤 User: {data.get('user','N/A')} | 🏷️ Role: {data.get('role','N/A')}\n\n"
                summary += f"📌 Action → `{json.dumps(data.get('action', {}))}`"

                table_data = None
                if isinstance(data, dict) and "result" in data:
                    result = data["result"]

                    if isinstance(result, list):
                        table_data = result
                        summary += f"\n\n📊 Found {len(result)} record(s)."
                    elif isinstance(result, dict):
                        table_data = [result]
                        summary += "\n\n📊 Found 1 record."
                    else:
                        summary += "\n\n⚠️ Unsupported format."
                else:
                    summary += "\n\n⚠️ No result found."

                st.session_state["chat_history"].append({
                    "role": "bot",
                    "content": summary,
                    "table_data": table_data
                })

            except json.JSONDecodeError:
                st.session_state["chat_history"].append({
                    "role": "bot",
                    "content": "❌ Invalid JSON response from backend.",
                    "table_data": None
                })
        else:
            st.session_state["chat_history"].append({
                "role": "bot",
                "content": f"❌ Backend error: {res.status_code}",
                "table_data": None
            })
        st.rerun()

    # Admin-only view
    token = st.session_state.get("access_token")
    res = api_get("/me/", token=token)
    if res.ok:
        user = res.json()
        with st.sidebar.expander("👤 Profile Info", expanded=True):
            st.write(f"**Username:** {user.get('username')}")
            st.write(f"**Role:** {user.get('user_category')}")

        if user.get("user_category") == "admin":
            st.sidebar.subheader("🛠️ Admin Tools")
            if st.sidebar.button("📋 Show All Tables"):
                res2 = api_get("/all-tables/", token=token)
                if res2.ok:
                    tables_data = res2.json()
                    if isinstance(tables_data, list) and len(tables_data) > 0:
                        st.markdown("### 📊 All Tables Data")
                        df = pd.DataFrame(tables_data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.json(tables_data)
                else:
                    st.error(f"Error: {res2.status_code}")

    else:
        st.error("Failed to fetch user info")
