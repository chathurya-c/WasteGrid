"""
Secure Database-Backed Authentication and Role-Based Access Control (RBAC) for WasteGrid 2.0.
- PBKDF2-HMAC-SHA256 password verification with unique salts
- Persistent user sessions in st.session_state
- Role and jurisdiction-based permission enforcement
- Change password & forgot password security workflows
- Admin user management hooks
"""

from datetime import datetime, timezone

import streamlit as st

from wastegrid import db
from wastegrid.components import render_html

# Official 5 Tenant Authority Roles
TENANT_ROLES_5 = [
    "State Waste Management Authority",
    "Municipal Commissioner",
    "Municipal Waste Officer",
    "Zonal Officer",
    "Waste Processing & Recycling Facility",
    "Municipal Truck Driver (In-Cab Logistics)",
]

# Legacy/Extended roles list
OFFICIAL_ROLES = [
    "State Waste Management Authority",
    "Municipal Commissioner",
    "Municipal Waste Officer",
    "Zonal Officer",
    "Waste Processing Facility",
    "Recycling Facility",
    "Municipal Truck Driver (In-Cab Logistics)",
]

# Canonical role matching dictionary
ROLE_CANONICAL = {
    "State Waste Management Authority": [
        "state",
        "state_authority",
        "State Waste Management Authority",
    ],
    "Municipal Commissioner": [
        "commissioner",
        "municipality",
        "Municipal Commissioner",
    ],
    "Municipal Waste Officer": [
        "waste_officer",
        "municipality",
        "Municipal Waste Officer",
    ],
    "Zonal Officer": ["zonal_officer", "district", "Zonal Officer"],
    "Waste Processing & Recycling Facility": [
        "processing_facility",
        "recycling_facility",
        "factory",
        "Waste Processing & Recycling Facility",
        "Waste Processing Facility",
        "Recycling Facility",
    ],
    "Waste Processing Facility": [
        "processing_facility",
        "factory",
        "Waste Processing Facility",
    ],
    "Recycling Facility": ["recycling_facility", "factory", "Recycling Facility"],
    "Municipal Truck Driver (In-Cab Logistics)": [
        "truck_driver",
        "driver_ramesh",
        "Municipal Truck Driver (In-Cab Logistics)",
        "Compactor Truck Driver (In-Cab Logistics)",
    ],
}

# Page-level role permissions matrix
BASE_PERMS = [
    "home",
    "services",
    "events",
    "map",
    "alerts",
    "reports",
    "settings",
    "logout",
    "overview",
    "operations",
    "allocation",
    "analytics",
    "alerts_citizen",
    "admin_reports",
    "facilities",
    "vehicles",
    "calendar",
    "carbon",
    "profile",
]

ROLE_PERMISSIONS = {
    "admin": BASE_PERMS + ["users", "simulator", "performance"],
    "state": BASE_PERMS,
    "state_authority": BASE_PERMS,
    "commissioner": BASE_PERMS,
    "municipality": BASE_PERMS + ["citizen_reports", "simulator"],
    "waste_officer": BASE_PERMS + ["citizen_reports"],
    "zonal_officer": BASE_PERMS + ["citizen_reports"],
    "district": BASE_PERMS + ["citizen_reports"],
    "processing_facility": BASE_PERMS,
    "factory": BASE_PERMS,
    "recycling_facility": BASE_PERMS,
    "truck_driver": [
        "home",
        "driver_in_cab",
        "driver_route",
        "driver_pass",
        "alerts",
        "settings",
        "logout",
        "profile",
    ],
}


def get_current_user():
    """Retrieve the current authenticated user record from session state or query param, synced with SQLite."""
    user = st.session_state.get("authenticated_user")
    if not user and hasattr(st, "query_params") and "u" in st.query_params:
        u_param = st.query_params.get("u")
        if u_param:
            db_user = db.get_user_by_username(str(u_param).strip().lower())
            if db_user and db_user.get("is_active"):
                st.session_state["authenticated_user"] = db_user
                user = db_user
    if user and isinstance(user, dict) and "username" in user:
        db_user = db.get_user_by_username(user["username"])
        if db_user:
            st.session_state["authenticated_user"] = db_user
            if hasattr(st, "query_params"):
                st.query_params["u"] = user["username"]
            return db_user
    return user


def is_authenticated():
    """Check if a valid active session exists."""
    user = get_current_user()
    return bool(user and user.get("is_active"))


def login(username, password, selected_role=None):
    """Authenticate against SQLite database with hashed password verification and role assignment."""
    clean_user = username.strip().lower()
    user = db.get_user_by_username(clean_user)
    if not user:
        return False, "Invalid Authority ID / Username or Password."

    if not user.get("is_active"):
        return (
            False,
            "This authority account has been deactivated by the system administrator.",
        )

    if not db.verify_password(password, user["password_hash"], user["salt"]):
        db.add_audit_log(username, "LOGIN_FAILED", "Incorrect password attempt")
        return False, "Invalid Authority ID / Username or Password."

    # Validate role if specified (and not auto-detect)
    if (
        selected_role
        and not selected_role.startswith("--")
        and user.get("role") != "admin"
    ):
        allowed_keys = ROLE_CANONICAL.get(selected_role, [selected_role])
        u_role = user.get("role", "")
        u_title = user.get("authority_title", "")
        if u_role not in allowed_keys and u_title != selected_role:
            return (
                False,
                f"Role Mismatch: Account '{username}' is registered as '{u_title}', not '{selected_role}'. Please select your assigned authority role.",
            )

    st.session_state["authenticated_user"] = user
    if hasattr(st, "query_params"):
        st.query_params["u"] = user["username"]
    if selected_role and not selected_role.startswith("--"):
        st.session_state["active_role_title"] = selected_role
    else:
        st.session_state["active_role_title"] = user.get(
            "authority_title", "Authorized Officer"
        )

    # Update last login timestamp in DB
    now_str = datetime.now(timezone.utc).isoformat()
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_str, user["id"]))
    conn.commit()
    conn.close()
    db.add_audit_log(
        user["username"],
        "LOGIN_SUCCESS",
        f"User logged in with role {user['role']} ({user.get('authority_title')})",
    )
    return True, "Login successful."


def logout():
    """Terminate the authenticated session and redirect directly to Home Dashboard."""
    user = get_current_user()
    if user:
        db.add_audit_log(user["username"], "LOGOUT", "User logged out")
    st.session_state.pop("authenticated_user", None)
    st.session_state["nav_selection"] = "home"
    st.session_state["show_auth_modal"] = False
    if hasattr(st, "query_params"):
        if "logout" in st.query_params:
            del st.query_params["logout"]
        if "u" in st.query_params:
            del st.query_params["u"]
        st.query_params["nav"] = "home"
    st.rerun()


def change_password(username, current_password, new_password, confirm_password):
    """Handle secure self-service password update."""
    if new_password != confirm_password:
        return False, "New passwords do not match."

    if len(new_password) < 8:
        return False, "Password must be at least 8 characters long."

    user = db.get_user_by_username(username)
    if not user:
        return False, "User not found."

    if not db.verify_password(current_password, user["password_hash"], user["salt"]):
        return False, "Current password verification failed."

    db.update_user_password(username, new_password)
    db.add_audit_log(username, "PASSWORD_CHANGED", "User successfully changed password")
    return (
        True,
        "Password updated successfully. Please use your new password next time.",
    )


def forgot_password_reset(username, verified_email, new_password, confirm_password):
    """Reset password if verified official email matches account record."""
    if new_password != confirm_password:
        return False, "New passwords do not match."

    if len(new_password) < 8:
        return False, "Password must be at least 8 characters long."

    user = db.get_user_by_username(username)
    if not user:
        return False, "No account found matching this username."

    if user["email"].strip().lower() != verified_email.strip().lower():
        return False, "Provided email address does not match official records on file."

    db.update_user_password(username, new_password)
    db.add_audit_log(
        username, "PASSWORD_RESET", "Password reset via verified email match"
    )
    return True, "Password reset successfully! You can now log in."


def has_permission(page_key):
    """Check if the current authenticated user has access to the specified page."""
    user = get_current_user()
    if not user:
        return False
    allowed_pages = ROLE_PERMISSIONS.get(user.get("role"), [])
    return page_key in allowed_pages


def render_sidebar_auth_widget():
    """
    Renders login form or current user profile in Streamlit's sidebar.
    """
    user = get_current_user()

    if user:
        # User is authenticated: Render user profile card in sidebar
        role_icons = {
            "state": "🏛️",
            "district": "📍",
            "municipality": "🏙️",
            "factory": "🏭",
            "admin": "🛡️",
        }
        u_icon = role_icons.get(user["role"], "👤")

        card_html = (
            f'<div style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); '
            f'border-radius: 8px; padding: 12px; margin-bottom: 16px;">'
            f'<div style="display:flex; align-items:center; gap:8px;">'
            f'<span style="font-size:1.4rem;">{u_icon}</span>'
            f'<div style="overflow:hidden;">'
            f'<div style="font-size:0.85rem; font-weight:700; text-overflow:ellipsis; white-space:nowrap;">{user["full_name"]}</div>'
            f'<div style="font-size:0.68rem; color:#8ba3c7; text-transform:uppercase; letter-spacing:0.08em;">{user["authority_title"]}</div>'
            f"</div></div>"
            f'<div style="margin-top:8px; font-size:0.68rem; color:#8ba3c7; border-top:1px solid rgba(255,255,255,0.06); padding-top:6px;">'
            f"<b>Scope:</b> {user['jurisdiction']}"
            f"</div></div>"
        )
        st.sidebar.markdown(card_html, unsafe_allow_html=True)

        col_out, col_pwd = st.sidebar.columns([1, 1])
        with col_out:
            if st.button("🚪 Logout", key="btn_sb_logout", use_container_width=True):
                logout()
        with col_pwd:
            if st.button("🔑 Profile", key="btn_sb_profile", use_container_width=True):
                st.session_state["nav_selection"] = "profile"
                st.rerun()

    else:
        # User is NOT authenticated: Render secure login card in sidebar
        st.sidebar.markdown(
            """
            <div style="margin-bottom:12px; font-size:0.8rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#8ba3c7;">
                🔐 Secure Authority Sign-In
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.sidebar.form("sb_login_form"):
            uname = st.text_input("Username", placeholder="e.g. municipality_admin")
            pword = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Sign In ➔", use_container_width=True)

            if submit:
                if uname and pword:
                    success, msg = login(uname, pword)
                    if success:
                        st.toast("✅ Signed in successfully!")
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter both username and password.")

        with st.sidebar.expander("❓ Forgot Password", expanded=False):
            st.markdown(
                "<small style='color:#8ba3c7;'>Official account recovery via verified email:</small>",
                unsafe_allow_html=True,
            )
            with st.form("sb_forgot_form"):
                f_user = st.text_input("Account Username")
                f_mail = st.text_input("Registered Official Email")
                f_p1 = st.text_input("New Password", type="password")
                f_p2 = st.text_input("Confirm New Password", type="password")
                f_sub = st.form_submit_button(
                    "Reset Password", use_container_width=True
                )
                if f_sub:
                    s, m = forgot_password_reset(f_user, f_mail, f_p1, f_p2)
                    if s:
                        st.success(m)
                    else:
                        st.error(m)


def register_account(
    username,
    password,
    full_name,
    email,
    role="municipality",
    jurisdiction="City Ward Operations",
    authority_title=None,
):
    """Register a new user account and log in immediately."""
    if len(username.strip()) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if "@" not in email:
        return False, "Please provide a valid email address."

    role_titles = {
        "admin": "System Administrator",
        "state": "State Waste Management Authority",
        "state_authority": "State Waste Management Authority",
        "district": "Zonal Officer",
        "commissioner": "Municipal Commissioner",
        "waste_officer": "Municipal Waste Officer",
        "municipality": "Municipal Waste Officer",
        "zonal_officer": "Zonal Officer",
        "processing_facility": "Waste Processing Facility",
        "factory": "Waste Processing Facility",
        "recycling_facility": "Recycling Facility",
        "truck_driver": "Municipal Truck Driver (In-Cab Logistics)",
    }
    title = authority_title or role_titles.get(role, "Municipal Waste Officer")

    clean_un = username.strip().lower()
    existing = db.get_user_by_username(clean_un)
    if existing:
        h, s = db.hash_password(password)
        conn = db.get_connection()
        c = conn.cursor()
        c.execute(
            """
            UPDATE users 
            SET password_hash = ?, salt = ?, role = ?, authority_title = ?, jurisdiction = ?, full_name = ?, email = ?
            WHERE username = ?
        """,
            (h, s, role, title, jurisdiction, full_name, email, clean_un),
        )
        conn.commit()
        conn.close()
    else:
        success, msg = db.create_user(
            clean_un, password, role, title, jurisdiction, full_name, email
        )
        if not success:
            return False, msg

    # Auto-login after creation or update
    user = db.get_user_by_username(clean_un)
    if user:
        st.session_state["authenticated_user"] = user
        st.session_state["active_role_title"] = title
        db.add_audit_log(
            clean_un,
            "USER_REGISTERED",
            f"User registered/updated and logged in with role {role} ({title})",
        )
        return True, f"Account configured successfully! Logged in as {title}."
    return True, "Account created successfully."


@st.dialog("👤 WasteGrid Authority Portal", width="large")
def show_auth_dialog(palette):
    """
    Native Streamlit modal dialog for Sign In, Create Account, or Active Profile.
    Opens when the Profile icon is clicked in the header.
    Supports all 5 tenant roles with real database authentication.
    """
    p = palette
    user = get_current_user()

    if user:
        # User is already signed in
        role_colors = {
            "admin": "#ef4444",
            "state": "#3b82f6",
            "state_authority": "#3b82f6",
            "commissioner": "#0284c7",
            "district": "#8b5cf6",
            "zonal_officer": "#8b5cf6",
            "municipality": "#10b981",
            "waste_officer": "#10b981",
            "factory": "#f59e0b",
            "processing_facility": "#f59e0b",
            "recycling_facility": "#10b981",
        }
        r_col = role_colors.get(user["role"], "#3b82f6")
        full_name = (
            user.get("full_name") or user.get("username") or "Authorized Officer"
        )
        initial_char = full_name[:1].upper()

        st.markdown(
            f"""
            <div style="background:{p["bg_soft"]}; border:1px solid {p["border"]}; border-radius:12px; padding:20px; line-height:1.8; font-size:0.88rem; margin-bottom:16px;">
                <div style="display:flex; align-items:center; gap:14px; margin-bottom:14px;">
                    <div style="width:48px; height:48px; border-radius:50%; background:{r_col}; color:#fff; display:flex; align-items:center; justify-content:center; font-size:1.4rem; font-weight:800; box-shadow:0 2px 8px rgba(0,0,0,0.25);">
                        {initial_char}
                    </div>
                    <div>
                        <div style="font-size:1.15rem; font-weight:800; color:{p["text"]};">{full_name}</div>
                        <span style="background:{r_col}; color:#fff; padding:3px 10px; border-radius:999px; font-size:0.72rem; font-weight:700; text-transform:uppercase;">
                            {user.get("authority_title", user.get("role", "Authority"))}
                        </span>
                    </div>
                </div>
                <div><b>Username / Authority ID:</b> <code>{user.get("username")}</code></div>
                <div><b>Designated Authority Role:</b> {user.get("authority_title")}</div>
                <div><b>Jurisdiction Scope:</b> {user.get("jurisdiction")}</div>
                <div><b>Official Email:</b> {user.get("email")}</div>
                <div><b>Account Verification:</b> <span style="color:#10b981; font-weight:700;">● Active Verified Official</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("🔄 Switch / Update Authority Role", expanded=True):
            current_title = user.get("authority_title") or "Municipal Waste Officer"
            idx = (
                TENANT_ROLES_5.index(current_title)
                if current_title in TENANT_ROLES_5
                else 0
            )
            with st.form("dlg_switch_role_form"):
                new_title = st.selectbox(
                    "Designated Authority Role",
                    TENANT_ROLES_5,
                    index=idx,
                    key="dlg_switch_role_sel",
                )
                btn_sw = st.form_submit_button(
                    "⚡ Update My Role & Switch View",
                    type="primary",
                    use_container_width=True,
                )
                if btn_sw:
                    role_key_map = {
                        "State Waste Management Authority": "state_authority",
                        "Municipal Commissioner": "commissioner",
                        "Municipal Waste Officer": "waste_officer",
                        "Zonal Officer": "zonal_officer",
                        "Waste Processing & Recycling Facility": "processing_facility",
                        "Municipal Truck Driver (In-Cab Logistics)": "truck_driver",
                    }
                    new_internal = role_key_map.get(new_title, "waste_officer")
                    conn = db.get_connection()
                    c = conn.cursor()
                    c.execute(
                        "UPDATE users SET role = ?, authority_title = ? WHERE id = ?",
                        (new_internal, new_title, user["id"]),
                    )
                    conn.commit()
                    conn.close()
                    st.session_state["authenticated_user"] = db.get_user_by_username(
                        user["username"]
                    )
                    st.session_state["active_role_title"] = new_title
                    st.session_state["show_auth_modal"] = False
                    if new_internal == "truck_driver":
                        st.session_state["nav_selection"] = "driver_in_cab"
                    else:
                        st.session_state["nav_selection"] = "home"
                    st.toast(f"✅ Switched role to: {new_title}")
                    st.rerun()

        with st.expander("🔑 Change Account Password", expanded=False):
            with st.form("dlg_change_pwd_form"):
                cur_p = st.text_input("Current Password", type="password")
                new_p = st.text_input("New Secure Password", type="password")
                cfm_p = st.text_input("Confirm New Password", type="password")
                sub_pwd = st.form_submit_button(
                    "Update Password ➔", use_container_width=True
                )
                if sub_pwd:
                    s, m = change_password(user["username"], cur_p, new_p, cfm_p)
                    if s:
                        st.success(m)
                    else:
                        st.error(m)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button(
                "🚪 Logout of Account",
                key="btn_dlg_logout_action",
                type="primary",
                use_container_width=True,
            ):
                st.session_state["show_auth_modal"] = False
                logout()
        with col_b2:
            if st.button(
                "✖️ Close Profile", key="btn_dlg_close_action", use_container_width=True
            ):
                st.session_state["show_auth_modal"] = False
                st.rerun()

    else:
        from wastegrid import theme as theme_module

        logo_uri = theme_module.get_logo_data_uri()
        render_html(
            f"""
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:14px; padding-bottom:8px; border-bottom:1px solid {p["border"]};">
                <img src="{logo_uri}" alt="WasteGrid Logo" style="width:36px; height:36px; object-fit:contain;" />
                <div>
                    <div style="font-size:1.05rem; font-weight:800; color:{p["text"]};">WasteGrid Authority Portal</div>
                    <div style="font-size:0.68rem; color:{p["muted"]}; font-weight:600; text-transform:uppercase; letter-spacing:0.08em;">Predict. Detect. Allocate.</div>
                </div>
            </div>
            """
        )

        # User is NOT signed in: Sign In, Sign Up, or 1-Click Fast Presets across 5 Tenants
        tab_login, tab_register, tab_forgot = st.tabs(
            [
                "🔑 Sign In (5 Tenants)",
                "📝 Sign Up (Create Account)",
                "❓ Forgot Password",
            ]
        )

        with tab_login:
            col_form, col_quick = st.columns([1.1, 1], gap="large")
            with col_form:
                render_html(
                    f'<div style="font-weight:700; color:{p["text"]}; margin-bottom:8px;">Authority Sign-In</div>'
                )
                with st.form("dlg_login_form"):
                    selected_role = st.selectbox(
                        "Authority Tenant Role",
                        ["-- Auto-Detect From Account --"] + TENANT_ROLES_5,
                        key="dlg_role_sel",
                    )
                    u_in = st.text_input(
                        "Authority ID / Username",
                        placeholder="e.g. commissioner, state_authority",
                        key="dlg_u_in",
                    )
                    p_in = st.text_input(
                        "Password",
                        type="password",
                        placeholder="••••••••",
                        key="dlg_p_in",
                    )
                    st.checkbox("Remember me", value=True, key="dlg_rem_me")

                    btn_login = st.form_submit_button(
                        "🔐 Sign In to Tenant Dashboard",
                        type="primary",
                        use_container_width=True,
                    )
                    if btn_login:
                        if u_in and p_in:
                            role_lookup = (
                                None
                                if selected_role.startswith("--")
                                else selected_role
                            )
                            if role_lookup == "Waste Processing & Recycling Facility":
                                role_lookup = "Waste Processing Facility"
                            ok, msg = login(u_in, p_in, selected_role=role_lookup)
                            if ok:
                                st.session_state["show_auth_modal"] = False
                                st.toast("✅ Signed in successfully!")
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.warning("Please enter both Username and Password.")

            with col_quick:
                render_html(
                    f"""
                    <div style="font-weight:800; color:{p["blue"]}; margin-bottom:4px; display:flex; align-items:center; gap:8px;">
                        <span>⚡ 1-Click Fast Tenant Logins</span>
                        <span style="background:rgba(239, 68, 68, 0.12); color:#ef4444; border:1px solid rgba(239, 68, 68, 0.3); font-size:0.65rem; padding:1px 7px; border-radius:999px; font-weight:800;">HACKATHON DEMO ONLY</span>
                    </div>
                    <div style="font-size:0.75rem; color:{p["muted"]}; margin-bottom:12px;">
                        Provided exclusively for hackathon judging convenience: Click any authority below to instantly review their dedicated dashboard and features without manual entry:
                    </div>
                    """
                )
                if st.button(
                    "🏛️ State Authority", use_container_width=True, key="btn_quick_t1"
                ):
                    login(
                        "state_authority",
                        "Waste@123",
                        selected_role="State Waste Management Authority",
                    )
                    st.session_state["show_auth_modal"] = False
                    st.rerun()
                if st.button(
                    "🏢 Municipal Commissioner",
                    use_container_width=True,
                    key="btn_quick_t2",
                ):
                    login(
                        "commissioner",
                        "Waste@123",
                        selected_role="Municipal Commissioner",
                    )
                    st.session_state["show_auth_modal"] = False
                    st.rerun()
                if st.button(
                    "🏙️ Municipal Waste Officer",
                    use_container_width=True,
                    key="btn_quick_t3",
                ):
                    login(
                        "waste_officer",
                        "Waste@123",
                        selected_role="Municipal Waste Officer",
                    )
                    st.session_state["show_auth_modal"] = False
                    st.rerun()
                if st.button(
                    "📍 Zonal Officer", use_container_width=True, key="btn_quick_t4"
                ):
                    login("zonal_officer", "Waste@123", selected_role="Zonal Officer")
                    st.session_state["show_auth_modal"] = False
                    st.rerun()
                if st.button(
                    "🏭 Processing & Recycling Plant",
                    use_container_width=True,
                    key="btn_quick_t5",
                ):
                    login(
                        "processing_facility",
                        "Waste@123",
                        selected_role="Waste Processing Facility",
                    )
                    st.session_state["show_auth_modal"] = False
                    st.rerun()
                if st.button(
                    "🚚 Truck Driver (Ramesh Kumar · KA-01-EA-101)",
                    use_container_width=True,
                    key="btn_quick_t6",
                ):
                    login(
                        "driver_ramesh",
                        "Driver@123",
                        selected_role="Municipal Truck Driver (In-Cab Logistics)",
                    )
                    st.session_state["show_auth_modal"] = False
                    st.session_state["nav_selection"] = "driver_in_cab"
                    st.rerun()

        with tab_register:
            st.markdown(
                f'<div style="font-weight:700; color:{p["text"]}; margin-bottom:8px;">Register Official Municipal Authority Account</div>',
                unsafe_allow_html=True,
            )
            with st.form("dlg_signup_form"):
                rc1, rc2 = st.columns(2)
                with rc1:
                    reg_fname = st.text_input(
                        "Full Official Name",
                        placeholder="e.g. Smt. Vandana Sharma",
                        key="reg_fn",
                    )
                    reg_uname = st.text_input(
                        "Desired Authority ID",
                        placeholder="e.g. vandana_officer",
                        key="reg_un",
                    )
                    reg_email = st.text_input(
                        "Official Email",
                        placeholder="officer@smartcity.gov.in",
                        key="reg_em",
                    )
                with rc2:
                    reg_role = st.selectbox(
                        "Authority Tenant Category",
                        TENANT_ROLES_5,
                        key="reg_role_sel",
                    )
                    reg_juris = st.text_input(
                        "Jurisdiction Scope / Ward",
                        placeholder="e.g. Central Zone Wards 101-120",
                        key="reg_ju",
                    )
                    reg_pwd1 = st.text_input(
                        "Password (min 6 chars)", type="password", key="reg_p1"
                    )
                    reg_pwd2 = st.text_input(
                        "Confirm Password", type="password", key="reg_p2"
                    )

                st.markdown(
                    f'<div style="font-size:0.75rem; color:{p["muted"]}; margin:8px 0 4px 0; font-weight:700;">🏭 NEW PROCESSING FACTORY COMMISSIONING (OPTIONAL — IF CONSTRUCTING NEW PLANT)</div>',
                    unsafe_allow_html=True,
                )
                fac_col1, fac_col2, fac_col3 = st.columns(3)
                with fac_col1:
                    new_fac_name = st.text_input(
                        "Factory / Plant Name",
                        placeholder="e.g. East Metro Bio-Methanation",
                        key="reg_fac_name",
                    )
                with fac_col2:
                    new_fac_type = st.selectbox(
                        "Plant Technology",
                        ["biocompost", "anaerobic_digester", "mrf", "waste_to_energy"],
                        key="reg_fac_type",
                    )
                    new_fac_stream = st.selectbox(
                        "Stream Intake", ["wet", "dry", "mixed"], key="reg_fac_stream"
                    )
                with fac_col3:
                    new_fac_cap = st.number_input(
                        "Design Capacity (kg/day)",
                        min_value=500.0,
                        max_value=50000.0,
                        value=3500.0,
                        step=500.0,
                        key="reg_fac_cap",
                    )

                btn_signup = st.form_submit_button(
                    "📝 Create Account & Commission Facility ➔",
                    type="primary",
                    use_container_width=True,
                )
                if btn_signup:
                    if not reg_uname or not reg_pwd1:
                        st.warning("Please fill in the required fields.")
                    elif reg_pwd1 != reg_pwd2:
                        st.error("Passwords do not match.")
                    else:
                        role_map = {
                            "State Waste Management Authority": "state_authority",
                            "Municipal Commissioner": "commissioner",
                            "Municipal Waste Officer": "waste_officer",
                            "Zonal Officer": "zonal_officer",
                            "Waste Processing & Recycling Facility": "processing_facility",
                            "Municipal Truck Driver (In-Cab Logistics)": "truck_driver",
                        }
                        internal_role = role_map.get(reg_role, "waste_officer")

                        # If a new facility is being constructed, commission it to the database
                        final_juris = reg_juris or "City Operations"
                        if new_fac_name.strip():
                            existing_facs = db.get_all_facilities(include_offline=True)
                            existing_ids = [f["id"] for f in existing_facs]
                            # Auto-pick next available alphabet ID
                            next_id = "D"
                            for letter in ["D", "E", "F", "G", "H", "K"]:
                                if letter not in existing_ids:
                                    next_id = letter
                                    break
                            db.add_facility(
                                next_id,
                                new_fac_name.strip(),
                                new_fac_type,
                                new_fac_stream,
                                float(new_fac_cap),
                                11.2,
                                12.9350,
                                77.6100,
                                "06:00 - 22:00",
                                96.0,
                                320.0,
                                0.04,
                            )
                            final_juris = f"Plant {next_id} ({new_fac_name.strip()})"
                            db.add_audit_log(
                                reg_uname,
                                "FACILITY_ONBOARDED",
                                f"Commissioned new Plant {next_id} ({new_fac_name.strip()}) with capacity {new_fac_cap} kg",
                            )

                        ok, msg = register_account(
                            reg_uname,
                            reg_pwd1,
                            reg_fname or reg_uname,
                            reg_email,
                            role=internal_role,
                            jurisdiction=final_juris,
                            authority_title=reg_role,
                        )
                        if ok:
                            st.session_state["show_auth_modal"] = False
                            st.session_state["nav_selection"] = "home"
                            if new_fac_name.strip():
                                st.toast(
                                    f"🎉 Account registered and Plant {next_id} commissioned to WasteGrid!"
                                )
                            else:
                                st.toast(
                                    "🎉 Account registered successfully and logged in!"
                                )
                            st.rerun()
                        else:
                            st.error(msg)

        with tab_forgot:
            st.markdown(
                f'<div style="font-weight:700; color:{p["text"]}; margin-bottom:8px;">Self-Service Password Recovery</div>',
                unsafe_allow_html=True,
            )
            st.caption(
                "Hint for demo accounts: `commissioner@bbmp.gov.in`, `driver.ramesh@wastegrid.gov.in`, `waste.officer@bbmp.gov.in`, `state.authority@wastegrid.gov.in`"
            )
            with st.form("dlg_forgot_form"):
                f_u = st.text_input(
                    "Account Authority ID / Username",
                    placeholder="e.g. driver_ramesh, commissioner",
                    key="f_un",
                )
                f_e = st.text_input(
                    "Registered Official Email",
                    placeholder="e.g. driver.ramesh@wastegrid.gov.in",
                    key="f_em",
                )
                f_p = st.text_input(
                    "New Password (min 8 chars)", type="password", key="f_np"
                )
                f_cp = st.text_input(
                    "Confirm New Password", type="password", key="f_ncp"
                )
                btn_f = st.form_submit_button(
                    "Reset Password ➔", use_container_width=True
                )
                if btn_f:
                    s, m = forgot_password_reset(f_u, f_e, f_p, f_cp)
                    if s:
                        st.success(m)
                    else:
                        st.error(m)


def render_auth_modal(palette):
    """Fallback wrapper that displays the modal dialog."""
    show_auth_dialog(palette)


def render_access_restricted_view(page_name):
    """Renders a clean notice when a user tries to access a page outside their role authority."""
    user = get_current_user()
    role_title = user["authority_title"] if user else "Public User"

    msg_html = (
        f'<div style="max-width: 650px; margin: 40px auto; text-align: center; background: rgba(255,56,86,0.06); '
        f'border: 1px solid rgba(255,56,86,0.3); border-radius: 12px; padding: 36px 28px;">'
        f'<div style="font-size: 2.8rem; margin-bottom: 12px;">🛡️</div>'
        f'<div style="font-size: 1.3rem; font-weight: 800; color: #ff3856; margin-bottom: 8px;">Jurisdictional Access Restricted</div>'
        f'<div style="font-size: 0.85rem; color: #8ba3c7; margin-bottom: 20px; line-height: 1.6;">'
        f"Your logged-in role as <b>{role_title}</b> does not have administrative clearance to access the <b>{page_name}</b> view."
        f"</div>"
        f'<div style="font-size: 0.75rem; color: #8ba3c7; background: rgba(0,0,0,0.2); padding: 12px; border-radius: 6px;">'
        f"Please contact the State Urban Development IT Administrator if you require elevated clearance."
        f"</div></div>"
    )
    st.markdown(msg_html, unsafe_allow_html=True)


def render_full_login_page(palette):
    """
    Renders the modern, full-screen WasteGrid Authority Login Page.
    Serves as the exclusive entry point of the website when unauthenticated.
    """
    p = palette

    # Waste-management themed background styling
    st.markdown(
        """
        <style>
        /* Hide sidebar when unauthenticated on login page */
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        .main .block-container {
            max-width: 900px !important;
            padding-top: 1.5rem !important;
            padding-bottom: 3rem !important;
        }
        .wg-login-brand {
            text-align: center;
            margin-bottom: 24px;
        }
        .wg-login-logo {
            width: 60px;
            height: 60px;
            margin: 0 auto 12px auto;
            border-radius: 16px;
            background: linear-gradient(135deg, #10b981 0%, #0284c7 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.2rem;
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.35);
        }
        .wg-login-title {
            font-size: 2.4rem;
            font-weight: 900;
            letter-spacing: -0.03em;
            line-height: 1.1;
            background: linear-gradient(135deg, #10b981, #38bdf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .wg-login-tagline {
            font-size: 0.95rem;
            font-weight: 800;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            color: #10b981;
            margin-top: 6px;
        }
        .wg-login-subtitle {
            font-size: 0.85rem;
            color: #8ba3c7;
            margin-top: 4px;
        }
        .wg-login-badge {
            display: inline-block;
            margin-top: 10px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 4px 14px;
            border-radius: 999px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #10b981;
        }
        .wg-login-card {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(16, 185, 129, 0.25);
            border-radius: 16px;
            padding: 28px 32px;
            box-shadow: 0 20px 45px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(12px);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    from wastegrid import theme as theme_module

    logo_uri = theme_module.get_logo_data_uri()

    # 1. Top Brand Header: WasteGrid Logo & Tagline
    st.markdown(
        f"""
        <div class="wg-login-brand">
            <img src="{logo_uri}" alt="WasteGrid Logo" style="width:78px; height:78px; margin:0 auto 12px auto; display:block; object-fit:contain; filter:drop-shadow(0 4px 14px rgba(0,0,0,0.25));" />
            <div class="wg-login-title">WasteGrid</div>
            <div class="wg-login-tagline">Predict. Detect. Allocate.</div>
            <div class="wg-login-subtitle">Intelligent Municipal Solid-Waste Management System</div>
            <div class="wg-login-badge">🛡️ Authorized Government & Municipal Access Only</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Centered Login Card
    col_l, col_c, col_r = st.columns([1, 1.8, 1])
    with col_c:
        st.markdown(
            f"""
            <div style="background:{p["card_bg"]}; border:1px solid {p["border"]}; border-radius:14px; padding:24px 28px; box-shadow:{p["shadow"]}; margin-bottom:18px;">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid {p["border"]}; padding-bottom:12px; margin-bottom:18px;">
                    <div>
                        <div style="font-size:1.15rem; font-weight:800; color:{p["text"]};">🏛️ Authority Sign-In</div>
                        <div style="font-size:0.75rem; color:{p["muted"]};">Enter your municipal credentials to access the grid</div>
                    </div>
                    <span style="font-size:0.68rem; font-weight:700; color:#10b981; background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); padding:2px 8px; border-radius:4px;">
                        256-bit PBKDF2
                    </span>
                </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("main_authority_login_form"):
            # 1. Authority ID / Username
            auth_user = st.text_input(
                "Authority ID / Username",
                placeholder="e.g. commissioner or state_authority",
                key="input_auth_user",
            )

            # 2. Password
            auth_pwd = st.text_input(
                "Password",
                type="password",
                placeholder="••••••••••••",
                key="input_auth_pwd",
            )

            # 3. Role Dropdown
            auth_role = st.selectbox(
                "Designated Authority Role",
                OFFICIAL_ROLES,
                index=0,
                key="select_auth_role",
            )

            # Remember Me Checkbox
            col_rem, col_blank = st.columns([1.2, 1])
            with col_rem:
                remember_me = st.checkbox(
                    "Remember this authority terminal",
                    value=True,
                    key="chk_auth_remember",
                )

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            # Prominent Login Button
            login_submitted = st.form_submit_button(
                "Access WasteGrid Dashboard ➔",
                type="primary",
                use_container_width=True,
            )

            if login_submitted:
                if not auth_user or not auth_pwd:
                    st.warning("⚠️ Please provide both Authority ID and Password.")
                else:
                    success, message = login(auth_user, auth_pwd, auth_role)
                    if success:
                        st.toast(
                            "✅ Authorized access granted. Redirecting to WasteGrid..."
                        )
                        st.session_state["nav_selection"] = "home"
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

        # Forgot Password Section
        with st.expander("❓ Forgot Password?", expanded=False):
            st.markdown(
                f"<div style='font-size:0.75rem; color:{p['muted']}; margin-bottom:8px;'>"
                "Self-service official password recovery via verified government email:"
                "</div>",
                unsafe_allow_html=True,
            )
            with st.form("login_page_forgot_form"):
                fgt_user = st.text_input("Account Authority ID / Username", key="fgt_u")
                fgt_email = st.text_input("Registered Official Email", key="fgt_e")
                fgt_p1 = st.text_input(
                    "New Secure Password", type="password", key="fgt_p1"
                )
                fgt_p2 = st.text_input(
                    "Confirm New Password", type="password", key="fgt_p2"
                )
                fgt_sub = st.form_submit_button(
                    "Reset Password", use_container_width=True
                )
                if fgt_sub:
                    if not fgt_user or not fgt_email or not fgt_p1:
                        st.warning("Please fill out all fields.")
                    else:
                        ok, msg = forgot_password_reset(
                            fgt_user, fgt_email, fgt_p1, fgt_p2
                        )
                        if ok:
                            st.success(f"✅ {msg}")
                        else:
                            st.error(f"❌ {msg}")

        # Restricted Registration Notice (No Public Registration)
        st.markdown(
            f"""
            <div style="margin-top:14px; padding-top:12px; border-top:1px solid {p["border"]}; font-size:0.72rem; color:{p["muted"]}; text-align:center; line-height:1.5;">
                🔒 <b>Restricted Authority Dashboard:</b> Public registration is disabled under Municipal Solid-Waste Regulations. 
                Accounts are provisioned solely to verified urban authorities, municipal commissioners, zonal officers, and facility directors.
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Evaluator & Auditor Fast Access Presets (1-Click Login for All 6 Roles)
        with st.expander(
            "⚡ Evaluator Quick-Login (1-Click Demo Presets)", expanded=True
        ):
            st.markdown(
                f"<div style='font-size:0.75rem; color:{p['muted']}; margin-bottom:10px;'>"
                "Click any designated authority below to sign in instantly with calibrated sample data:"
                "</div>",
                unsafe_allow_html=True,
            )

            col_q1, col_q2 = st.columns(2)
            with col_q1:
                if st.button(
                    "🏛️ State Authority", use_container_width=True, key="quick_state_btn"
                ):
                    login(
                        "state_authority",
                        "Waste@123",
                        "State Waste Management Authority",
                    )
                    st.session_state["nav_selection"] = "home"
                    st.rerun()

                if st.button(
                    "🏙️ Municipal Commissioner",
                    use_container_width=True,
                    key="quick_comm_btn",
                ):
                    login("commissioner", "Waste@123", "Municipal Commissioner")
                    st.session_state["nav_selection"] = "home"
                    st.rerun()

                if st.button(
                    "📋 Municipal Waste Officer",
                    use_container_width=True,
                    key="quick_wo_btn",
                ):
                    login("waste_officer", "Waste@123", "Municipal Waste Officer")
                    st.session_state["nav_selection"] = "home"
                    st.rerun()

            with col_q2:
                if st.button(
                    "📍 Zonal Officer", use_container_width=True, key="quick_zo_btn"
                ):
                    login("zonal_officer", "Waste@123", "Zonal Officer")
                    st.session_state["nav_selection"] = "home"
                    st.rerun()

                if st.button(
                    "🏭 Waste Processing Facility",
                    use_container_width=True,
                    key="quick_pf_btn",
                ):
                    login(
                        "processing_facility", "Waste@123", "Waste Processing Facility"
                    )
                    st.session_state["nav_selection"] = "home"
                    st.rerun()

                if st.button(
                    "♻️ Recycling Facility", use_container_width=True, key="quick_rf_btn"
                ):
                    login("recycling_facility", "Waste@123", "Recycling Facility")
                    st.session_state["nav_selection"] = "home"
                    st.rerun()

    # Subtle Footer for Login Page
    st.markdown(
        f"""
        <div style="text-align:center; font-size:0.73rem; color:{p["muted"]}; margin-top:32px;">
            WasteGrid · Predict. Detect. Allocate. · © 2026 Municipal SWM Directorate. All rights reserved.
        </div>
        """,
        unsafe_allow_html=True,
    )
