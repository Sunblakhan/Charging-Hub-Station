# -----------------------------------------------------------------------------
import os
import time
import pandas as pd
import streamlit as st

# --- SET CURRENT WORKING DIRECTORY ---
currentWorkingDirectory = os.path.dirname(os.path.abspath(__file__))
os.chdir(currentWorkingDirectory)

# --- LOCAL IMPORTS ---
from core import methods as m1
from core import HelperTools as ht
from config import pdict
from src.malfunction.ui.malfunction_ui import show_malfunction_page, has_open_malfunctions
from src.rating.ui.rating_ui import show_rating_page

# --- AUTH IMPORTS ---
from src.auth.auth_handler import AuthHandler

# -----------------------------------------------------------------------------
# UI CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
def setup_style():
    """Injects custom CSS to beautify the application and FIX button colors."""
    st.markdown("""
        <style>
        /* 1. RESET & MAIN CONTAINER */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        
        /* 2. SIDEBAR REFINEMENT */
        [data-testid="stSidebar"] {
            background-color: #f8f9fa;
            border-right: 1px solid #e9ecef;
        }
        [data-testid="stSidebar"] hr {
            margin: 1rem 0;
            border-color: #e9ecef;
        }
        
        /* 3. ADMIN PANEL CARD */
        .admin-card {
            background-color: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid #f1f3f5;
            margin-bottom: 16px;
        }
        
        /* 4. STATUS BADGE */
        .status-badge {
            background-color: #e3f2fd; /* Light Blue */
            color: #1565c0;           /* Dark Blue Text */
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            border: 1px solid #bbdefb;
        }

        /* 5. FORCE PRIMARY BUTTON TO BE GREEN (Fixes the Red Issue) */
        button[kind="primary"] {
            background-color: #2e7d32 !important; /* Green */
            border-color: #2e7d32 !important;
            color: white !important;
            transition: all 0.2s ease-in-out;
        }
        button[kind="primary"]:hover {
            background-color: #1b5e20 !important; /* Darker Green on Hover */
            border-color: #1b5e20 !important;
            box-shadow: 0 4px 12px rgba(46, 125, 50, 0.2);
        }

        /* 6. STYLE THE REJECT BUTTON (Secondary) */
        button[kind="secondary"] {
            border-color: #dee2e6 !important;
            color: #495057 !important;
        }
        button[kind="secondary"]:hover {
            border-color: #ff6b6b !important; /* Red Border on Hover */
            color: #e03131 !important;        /* Red Text on Hover */
            background-color: #fff5f5 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# HELPER: Admin Panel UI 
# -----------------------------------------------------------------------------
def render_admin_panel(auth):
    st.title("🛡️ Admin Dashboard")
    
    # 1. Get Data
    pending_users = auth.get_pending_operators()
    count = len(pending_users)

    # 2. Header Stats (Cleaner than st.metric)
    if not pending_users:
        st.success("✅ All caught up! No pending requests.")
        return

    # A simple, clean header showing the count
    st.markdown(f"### 🔔 **{count}** Pending Request{'s' if count != 1 else ''}")
    st.caption("Review the details below to authorize new station operators.")
    st.markdown("---")

    # 3. Display Requests as "Cards"
    for email, station_label in pending_users:
        # Create a card container
        with st.container(border=True):
            # ADJUSTED COLUMN RATIOS: 
            # [0.6] -> Small, tight column for the Avatar
            # [3.5] -> Wide column for Email & Station info
            # [1.2] -> Specific width for Buttons so they aren't too stretched
            col_icon, col_info, col_btn = st.columns([0.6, 3.5, 1.2])
            
            # --- LEFT: AVATAR ---
            with col_icon:
                # Centered, circular avatar with soft colors
                st.markdown("""
                    <div style='
                        background-color: #f8f9fa;
                        color: #495057;
                        width: 48px;
                        height: 48px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 22px;
                        border: 1px solid #dee2e6;
                        margin-top: 5px;'>
                        👤
                    </div>
                """, unsafe_allow_html=True)

            # --- MIDDLE: USER INFO ---
            with col_info:
                # Email (Bold, slightly larger)
                st.markdown(f"<div style='font-size: 1.1rem; font-weight: 600; color: #212529; margin-bottom: 2px;'>{email}</div>", unsafe_allow_html=True)
                
                # Station (Grey text with icon)
                if station_label:
                    st.markdown(f"<div style='color: #6c757d; font-size: 0.9rem; margin-bottom: 8px;'>📍 {station_label}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='color: #dc3545; font-size: 0.9rem; margin-bottom: 8px;'>⚠️ <b>No Station Selected</b></div>", unsafe_allow_html=True)

                # Badge (Inline styled for perfect alignment)
                st.markdown(f"""
                    <span style='
                        background-color: #e3f2fd; 
                        color: #0d47a1; 
                        padding: 4px 10px; 
                        border-radius: 12px; 
                        font-size: 0.75rem; 
                        font-weight: 700;
                        letter-spacing: 0.5px;'>
                        ⏳ PENDING APPROVAL
                    </span>
                """, unsafe_allow_html=True)

            # --- RIGHT: ACTIONS ---
            with col_btn:
                # Vertical alignment helper (pushes buttons to center vertically if needed)
                # st.write("") 
                
                # APPROVE
                if st.button("✓ Approve", key=f"app_{email}", type="primary", use_container_width=True):
                    if auth.approve_operator(email):
                        st.toast(f"✅ Approved {email}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Database error.")

                # REJECT (Added a tiny margin-top via markdown if needed, but standard stacking usually looks good)
                if st.button("✕ Reject", key=f"rej_{email}", use_container_width=True):
                    if auth.reject_operator(email):
                        st.toast(f"🗑️ Rejected {email}")
                        time.sleep(1)
                        st.rerun()
# -----------------------------------------------------------------------------
# MAIN APP
# -----------------------------------------------------------------------------
@ht.timer
def main():
    st.set_page_config(
        page_title="Berlin Charging Hub Portal", 
        page_icon="⚡", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inject CSS
    setup_style()
    
    # Initialize Auth Handler
    auth = AuthHandler()

    # --- 1. SESSION STATE INITIALIZATION -------------------------------------
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    # --- 2. AUTHENTICATION SCREEN --------------------------------------------
    if st.session_state['user'] is None:
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("⚡ Berlin Charging Hub Portal")
            
            # Tabs for Login/Signup
            tab_login, tab_signup = st.tabs(["🔐 Login", "📝 Sign Up"])

            # --- TAB 1: LOGIN ---
            with tab_login:
                with st.form("login_form"):
                    email = st.text_input("Email", key="login_email")
                    password = st.text_input("Password", type="password", key="login_pass")
                    
                    st.write("") # Spacer
                    submitted_login = st.form_submit_button("Sign In", type="primary", use_container_width=True)
                    
                    if submitted_login:
                        user, msg = auth.login(email, password)
                        if user:
                            st.session_state['user'] = user
                            st.toast("Login successful!", icon="✅")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(msg)

            # --- TAB 2: SIGN UP ---
            with tab_signup:
                st.write("Create a new account.")
                
                # Initialize reset counter if not present
                if "signup_form_id" not in st.session_state:
                    st.session_state.signup_form_id = 0
                
                # Helper to shorten variable name
                sid = st.session_state.signup_form_id

                # Role Selection
                # Key changes on success -> resets selection to default ("user")
                role_choice = st.selectbox(
                    "I am a:", 
                    ["user", "operator"], 
                    format_func=lambda x: "Regular User" if x == "user" else "Station Operator", 
                    key=f"signup_role_{sid}"
                )
                
                # Dynamic Station Selection
                selected_station = None
                if role_choice == "operator":
                    st.info("Please select your assigned station.")
                    try:
                        df_geo_raw = pd.read_csv(os.path.join("datasets", pdict["file_lstations"]), sep=';', encoding='utf-8', header=0)
                        
                        # Filter for Berlin stations (ending in " Berlin")
                        df_signup_berlin = df_geo_raw[
                            df_geo_raw["station_label"].astype(str).str.contains(r' Berlin\s*$', case=False, regex=True, na=False)
                        ]

                        signup_station_options = sorted(df_signup_berlin["station_label"].unique())
                        
                        # Key changes on success -> resets selection
                        selected_station = st.selectbox(
                            "Assigned Station", 
                            signup_station_options, 
                            key=f"signup_station_{sid}", 
                            index=None, 
                            placeholder="Search station..."
                        )
                    except Exception as e:
                        st.error(f"Error loading stations: {e}")

                # Inputs with Dynamic Keys
                new_email = st.text_input("Email", key=f"signup_email_{sid}")
                new_pass = st.text_input("Password", type="password", key=f"signup_pass_{sid}")
                confirm_pass = st.text_input("Confirm Password", type="password", key=f"signup_confirm_{sid}")
                
                st.write("")
                if st.button("Create Account", type="primary", use_container_width=True):
                    # --- VALIDATION LOGIC ---
                    
                    if not new_email.strip():
                        st.error("⚠️ Email field cannot be empty.")
                        
                    elif not new_pass.strip():
                        st.error("⚠️ Password field cannot be empty.")
                        
                    elif new_pass != confirm_pass:
                        st.error("⚠️ Passwords do not match!")
                        
                    elif len(new_pass) < 4:
                        st.error("⚠️ Password is too short! (Minimum 4 characters)")
                        
                    elif role_choice == "operator" and not selected_station:
                        st.error("❌ You must select a station to sign up as an Operator.")
                        
                    else:
                        success, msg = auth.signup(new_email, new_pass, role=role_choice, station_label=selected_station)
                        
                        if success:
                            if role_choice == 'user':
                                st.success("✅ Account created! Please switch to the Login tab.")
                            else:
                                st.warning("⏳ Account created! Waiting for Admin approval.")
                            
                            # --- RESET FIELDS ---
                            st.session_state.signup_form_id += 1
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error(f"⚠️ {msg}")
                            
        return  # Stop execution here

    # --- 3. LOGGED IN SIDEBAR (Enhanced) -------------------------------------
    current_user = st.session_state['user']
    
    with st.sidebar:
        # Custom Profile Card
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
            padding: 20px; 
            border-radius: 12px; 
            border: 1px solid #dee2e6; 
            margin-bottom: 20px;
            text-align: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">👤</div>
            <div style="font-weight: 700; color: #212529; word-break: break-all;">{current_user.email}</div>
            <div style="
                display: inline-block;
                margin-top: 8px;
                background-color: {'#2e7d32' if current_user.role == 'admin' else '#1565c0'};
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-weight: 600;">
                {current_user.role}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("Menu")
        
        options = ["Map", "Ratings", "Malfunction"]
        # Add Admin Panel if Admin
        if current_user.role == "admin":
            options.insert(0, "Admin Panel")
            
        page_selection = st.radio("Go to", options, label_visibility="collapsed")

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['user'] = None
            st.rerun()

    # --- 4. PAGE ROUTING -----------------------------------------------------
    
    # A) ADMIN PANEL
    if page_selection == "Admin Panel":
        if current_user.role == "admin":
            render_admin_panel(auth)
        else:
            st.error("⛔ Access Denied")

    # B) MAP
    elif page_selection == "Map":
        st.title("🗺️ Berlin Charging Heatmap")
        
        if has_open_malfunctions():
            st.warning("Some charging stations currently have reported malfunctions." " Please checkout malfunction station before visiting.", icon="⚠️")

        # Load Data
        df_geodat_plz = pd.read_csv(os.path.join("datasets", pdict["file_geodat_plz"]), sep=';', encoding='latin-1')
        df_lstat = pd.read_csv(os.path.join("datasets", pdict["file_lstations"]), sep=';', encoding='utf-8', header=0)
        
        # Process Data
        df_lstat2 = m1.preprop_lstat(df_lstat, df_geodat_plz, pdict)
        gdf_lstat3 = m1.count_plz_occurrences(df_lstat2)
        gdf_lstat3_kw = m1.count_plz_by_kw(df_lstat2)    
        df_residents = pd.read_csv(os.path.join("datasets", pdict["file_residents"]), encoding='latin-1')
        gdf_residents2 = m1.preprop_resid(df_residents, df_geodat_plz, pdict)
        
        # Render Map
        m1.make_streamlit_electric_Charging_resid(gdf_lstat3, gdf_residents2, gdf_lstat3_kw)

    # C) RATINGS
    elif page_selection == "Ratings":
        df_lstat = pd.read_csv(os.path.join("datasets", pdict["file_lstations"]), sep=';', encoding='utf-8', header=0)
        show_rating_page(df_lstat)

    # D) MALFUNCTION
    elif page_selection == "Malfunction":
        df_lstat = pd.read_csv(os.path.join("datasets", pdict["file_lstations"]), sep=';', encoding='utf-8', header=0)
        show_malfunction_page(df_lstat) 

if __name__ == "__main__": 
    main()