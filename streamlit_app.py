"""
CarePulse Health - Streamlit Deployment Application.
Reuses the modular Python backend (Database, AuthService, ChatbotEngine, MemoGenerator)
with a native Streamlit interface.
"""

import os
import sys
import datetime
import streamlit as st
import pandas as pd

# Add workspace directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import Database
from backend.auth_service import AuthService
from backend.chatbot_engine import ChatbotEngine
from backend.memo_generator import MemoGenerator
from backend.triage_engine import TriageEngine
from backend.models import Role, User


# ============================================================================
# Page Configuration & Styling
# ============================================================================
st.set_page_config(
    page_title="CarePulse Health - Doctor Appointment & Virtual Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished medical look
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0369a1;
        margin-bottom: 4px;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 24px;
    }
    .role-banner-guest {
        background-color: #f0fdf4;
        border-left: 5px solid #16a34a;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 20px;
        color: #14532d;
    }
    .role-banner-patient {
        background-color: #f0f9ff;
        border-left: 5px solid #0284c7;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 20px;
        color: #0c4a6e;
    }
    .role-banner-admin {
        background-color: #fefce8;
        border-left: 5px solid #ca8a04;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 20px;
        color: #713f12;
    }
    .doc-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Session State Initialization
# ============================================================================
if "db" not in st.session_state:
    st.session_state.db = Database()
if "auth" not in st.session_state:
    st.session_state.auth = AuthService()
if "chatbot" not in st.session_state:
    st.session_state.chatbot = ChatbotEngine(st.session_state.db)

if "role" not in st.session_state:
    st.session_state.role = "guest"
if "user" not in st.session_state:
    st.session_state.user = User(
        user_id="guest_init",
        username="guest_visitor",
        role=Role.GUEST,
        display_name="Guest Visitor"
    )
if "token" not in st.session_state:
    st.session_state.token = None

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = f"st_session_{os.getpid()}"


# ============================================================================
# Sidebar: Brand & Authentication
# ============================================================================
with st.sidebar:
    st.markdown("## 🏥 CarePulse Health")
    st.caption("Specialty Clinic & Virtual AI Assistant")
    st.markdown("---")

    # Current Status Badge
    role_display = st.session_state.role.upper()
    if st.session_state.role == "guest":
        st.info("👤 **Active Role:** GUEST")
    elif st.session_state.role == "patient":
        st.success(f"🩺 **Active Role:** PATIENT ({st.session_state.user.display_name})")
    elif st.session_state.role == "admin":
        st.warning("🛡️ **Active Role:** ADMINISTRATOR")

    st.markdown("### 🔑 Authentication / Switch Role")

    role_choice = st.radio(
        "Select Role:",
        ["Guest Mode", "Patient Login", "Admin Login"],
        index=0 if st.session_state.role == "guest" else (1 if st.session_state.role == "patient" else 2)
    )

    if role_choice == "Guest Mode":
        st.caption("✨ No credentials required. Instantly explore non-prescriptive wellness advice.")
        if st.session_state.role != "guest":
            if st.button("Continue as Guest", use_container_width=True):
                success, token, user, msg = st.session_state.auth.login(role="guest")
                st.session_state.role = "guest"
                st.session_state.user = user
                st.session_state.token = token
                st.session_state.chat_messages = []
                st.session_state.chatbot.reset_session(st.session_state.chat_session_id)
                st.rerun()

    elif role_choice == "Patient Login":
        st.caption("🔑 **Standard Credentials:** `patient` / `healthcare`")
        u_input = st.text_input("Username", value="patient" if st.session_state.role != "patient" else st.session_state.user.username, key="pat_user")
        p_input = st.text_input("Password", value="healthcare" if st.session_state.role != "patient" else "healthcare", type="password", key="pat_pass")

        if st.button("Log In as Patient", type="primary", use_container_width=True):
            success, token, user, msg = st.session_state.auth.login(u_input, p_input, role="patient")
            if success:
                st.session_state.role = "patient"
                st.session_state.user = user
                st.session_state.token = token
                st.session_state.chat_messages = []
                st.session_state.chatbot.reset_session(st.session_state.chat_session_id)
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    elif role_choice == "Admin Login":
        st.caption("🛡️ **Standard Credentials:** `admin` / `admin`")
        adm_u = st.text_input("Username", value="admin" if st.session_state.role != "admin" else st.session_state.user.username, key="adm_user")
        adm_p = st.text_input("Password", value="admin" if st.session_state.role != "admin" else "admin", type="password", key="adm_pass")

        if st.button("Log In as Admin", type="primary", use_container_width=True):
            success, token, user, msg = st.session_state.auth.login(adm_u, adm_p, role="admin")
            if success:
                st.session_state.role = "admin"
                st.session_state.user = user
                st.session_state.token = token
                st.session_state.chat_messages = []
                st.session_state.chatbot.reset_session(st.session_state.chat_session_id)
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.markdown("---")
    if st.session_state.role != "guest":
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.auth.logout(st.session_state.token)
            st.session_state.role = "guest"
            st.session_state.user = User(
                user_id="guest_init",
                username="guest_visitor",
                role=Role.GUEST,
                display_name="Guest Visitor"
            )
            st.session_state.token = None
            st.session_state.chat_messages = []
            st.session_state.chatbot.reset_session(st.session_state.chat_session_id)
            st.rerun()

    # Navigation menu
    st.markdown("### 📌 Navigation")
    nav_options = ["🤖 HealthBot Assistant", "👨‍⚕️ Doctors Directory"]
    if st.session_state.role in ["patient", "admin"]:
        nav_options.append("📋 My Appointments")
    if st.session_state.role == "admin":
        nav_options.append("📊 Admin Dashboard")

    selected_nav = st.radio("Go to:", nav_options, index=0)


# ============================================================================
# Main Section: Navigation Dispatcher
# ============================================================================

# ----------------------------------------------------------------------------
# 1. HealthBot Virtual Care Assistant
# ----------------------------------------------------------------------------
if selected_nav == "🤖 HealthBot Assistant":
    st.markdown('<div class="main-title">HealthBot Virtual Care Assistant</div>', unsafe_allow_html=True)

    # Role Context Banner
    if st.session_state.role == "guest":
        st.markdown("""
        <div class="role-banner-guest">
            🌿 <strong>Guest Wellness Mode:</strong> Ask for lifestyle, sleep, posture, hydration, or stress tips.<br>
            ⚠️ <em>Policy: In Guest mode, HealthBot provides non-prescriptive wellness advice only and strictly refuses medications or prescriptions. Log in as Patient to book doctor appointments!</em>
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state.role == "patient":
        st.markdown(f"""
        <div class="role-banner-patient">
            🩺 <strong>Patient Mode Active ({st.session_state.user.display_name}):</strong> Clinical triage enabled.<br>
            Tell HealthBot your symptoms. It will identify the appropriate specialist, verify doctor availability, book your slot, and generate a downloadable booking confirmation memo!
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state.role == "admin":
        st.markdown("""
        <div class="role-banner-admin">
            🛡️ <strong>Admin Oversight Mode:</strong> Query live clinic statistics, doctor schedules, or override appointment cancellations.
        </div>
        """, unsafe_allow_html=True)

    # Quick Action Chips
    st.markdown("**⚡ Quick Prompts:**")
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

    preset_query = None
    with quick_col1:
        if st.session_state.role == "guest":
            if st.button("🌙 Sleep hygiene tips", use_container_width=True):
                preset_query = "Tips for better sleep"
        else:
            if st.button("🩺 Check symptoms & book", use_container_width=True):
                preset_query = "Check symptoms & book appointment"

    with quick_col2:
        if st.session_state.role == "guest":
            if st.button("💧 Hydration advice", use_container_width=True):
                preset_query = "Hydration guidelines"
        else:
            if st.button("📋 My appointments", use_container_width=True):
                preset_query = "My appointments"

    with quick_col3:
        if st.session_state.role == "guest":
            if st.button("💊 Ask for medication", use_container_width=True):
                preset_query = "Can you prescribe some medicine for my headache?"
        else:
            if st.button("❌ Cancel appointment", use_container_width=True):
                preset_query = "Cancel my appointment"

    with quick_col4:
        if st.button("🔄 Reset Chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.session_state.chatbot.reset_session(st.session_state.chat_session_id)
            st.rerun()

    # Initial Welcome Message if Chat is Empty
    if not st.session_state.chat_messages:
        welcome_resp = st.session_state.chatbot.process_message(
            st.session_state.chat_session_id,
            st.session_state.user,
            "start over"
        )
        st.session_state.chat_messages.append({"sender": "bot", "text": welcome_resp.reply})

    # Render Chat History
    for msg in st.session_state.chat_messages:
        if msg["sender"] == "user":
            with st.chat_message("user"):
                st.write(msg["text"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(msg["text"])

                # Render Card if present
                if "card" in msg and msg["card"]:
                    card = msg["card"]
                    with st.expander(f"📋 {card.title} - {card.subtitle}", expanded=True):
                        for k, v in card.details.items():
                            st.write(f"**{k}:** {v}")

                # Render Download Memo Button if appointment confirmed
                if "memo_id" in msg and msg["memo_id"]:
                    memo_id = msg["memo_id"]
                    appt = st.session_state.db.get_appointment_by_id(memo_id)
                    if appt:
                        text_memo = MemoGenerator.generate_text_memo(appt)
                        html_memo = MemoGenerator.generate_html_memo(appt)

                        col_dl1, col_dl2 = st.columns(2)
                        with col_dl1:
                            st.download_button(
                                label="📥 Download Confirmation Memo (.TXT)",
                                data=text_memo,
                                file_name=f"CarePulse-Memo-{memo_id}.txt",
                                mime="text/plain",
                                key=f"dl_txt_{memo_id}_{len(st.session_state.chat_messages)}"
                            )
                        with col_dl2:
                            with st.expander("🖨️ View & Print Official Memo Slip"):
                                st.components.v1.html(html_memo, height=500, scrolling=True)

    # Handle User Input
    user_input = st.chat_input("Type your symptoms, wellness question, or cancellation request...")
    if preset_query:
        user_input = preset_query

    if user_input:
        # Display user message
        st.session_state.chat_messages.append({"sender": "user", "text": user_input})

        # Process with Chatbot Engine
        response = st.session_state.chatbot.process_message(
            st.session_state.chat_session_id,
            st.session_state.user,
            user_input
        )

        bot_msg = {
            "sender": "bot",
            "text": response.reply,
            "card": response.card,
            "memo_id": response.download_memo_id
        }
        st.session_state.chat_messages.append(bot_msg)
        st.rerun()


# ----------------------------------------------------------------------------
# 2. Doctors Catalog
# ----------------------------------------------------------------------------
elif selected_nav == "👨‍⚕️ Doctors Directory":
    st.markdown('<div class="main-title">Specialist Physicians Directory</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Explore qualifications, consultation fees, and available days across clinical specialties.</div>', unsafe_allow_html=True)

    specialties = ["All Specialties", "Cardiology", "Dermatology", "Neurology", "Orthopedics", "General Medicine", "Pediatrics", "ENT Specialist"]
    selected_spec = st.selectbox("Filter by Medical Specialty:", specialties)

    filter_spec = None if selected_spec == "All Specialties" else selected_spec
    doctors = st.session_state.db.get_doctors(filter_spec)

    cols = st.columns(2)
    for idx, doc in enumerate(doctors):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="doc-card">
                <h3>{doc.name}</h3>
                <span style="background:#e0f2fe; color:#0369a1; padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:700;">
                    {doc.specialty}
                </span>
                <p style="margin-top:8px; font-size:0.85rem; color:#64748b;"><strong>Qualifications:</strong> {doc.qualification}</p>
                <p style="font-size:0.88rem; color:#334155;">{doc.bio}</p>
                <div style="display:flex; justify-content:space-between; margin-top:10px; background:#f8fafc; padding:8px 12px; border-radius:6px; font-size:0.85rem;">
                    <span>⭐ <strong>{doc.rating} / 5.0</strong></span>
                    <span>Experience: <strong>{doc.experience_years} years</strong></span>
                    <span>Fee: <strong>${doc.fee:.2f}</strong></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.role == "patient":
                if st.button(f"📅 Book with {doc.name}", key=f"book_btn_{doc.id}"):
                    st.session_state.chat_messages.append({
                        "sender": "user",
                        "text": f"I want to book an appointment with {doc.name} for {doc.specialty}"
                    })
                    resp = st.session_state.chatbot.process_message(
                        st.session_state.chat_session_id,
                        st.session_state.user,
                        f"I want to book an appointment with {doc.name} for {doc.specialty}"
                    )
                    st.session_state.chat_messages.append({
                        "sender": "bot",
                        "text": resp.reply,
                        "card": resp.card
                    })
                    st.rerun()


# ----------------------------------------------------------------------------
# 3. My Booked Appointments (Patient / Admin)
# ----------------------------------------------------------------------------
elif selected_nav == "📋 My Appointments":
    st.markdown('<div class="main-title">Booked Consultations</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Review your appointment details, download confirmation memos, or request cancellations.</div>', unsafe_allow_html=True)

    if st.session_state.role == "patient":
        appts = st.session_state.db.get_appointments(patient_username=st.session_state.user.username)
    else:
        appts = st.session_state.db.get_appointments()

    if not appts:
        st.info("You currently do not have any appointments recorded. Use HealthBot to schedule a consultation!")
    else:
        for a in appts:
            with st.container():
                c1, c2, c3, c4 = st.columns([1.5, 2.5, 2, 2])
                with c1:
                    st.markdown(f"**ID:** `{a.id}`")
                    status_color = "green" if a.status.value == "CONFIRMED" else ("red" if a.status.value == "CANCELLED" else "gray")
                    st.markdown(f":{status_color}[**{a.status.value}**]")
                with c2:
                    st.markdown(f"**Doctor:** {a.doctor_name}")
                    st.caption(f"Specialty: {a.specialty} | Patient: {a.patient_name}")
                with c3:
                    st.markdown(f"🗓️ **{a.date}**")
                    st.caption(f"Time Slot: {a.time_slot}")
                with c4:
                    col_act1, col_act2 = st.columns(2)
                    with col_act1:
                        memo_text = MemoGenerator.generate_text_memo(a)
                        st.download_button(
                            label="📥 Memo",
                            data=memo_text,
                            file_name=f"Memo-{a.id}.txt",
                            mime="text/plain",
                            key=f"memo_btn_{a.id}"
                        )
                    with col_act2:
                        if a.status.value == "CONFIRMED":
                            if st.button("❌ Cancel", key=f"cancel_btn_{a.id}"):
                                success, updated_a, msg = st.session_state.db.cancel_appointment(
                                    a.id,
                                    user_role=st.session_state.role,
                                    username=st.session_state.user.username,
                                    reason="Cancelled via portal"
                                )
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                st.markdown("---")


# ----------------------------------------------------------------------------
# 4. Admin Dashboard (Admin Only)
# ----------------------------------------------------------------------------
elif selected_nav == "📊 Admin Dashboard":
    st.markdown('<div class="main-title">Hospital Executive Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Real-time scheduling metrics, departmental volume, and clinical workload.</div>', unsafe_allow_html=True)

    stats = st.session_state.db.get_statistics()

    # KPI Metrics
    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
    kpi1.metric("Total Appointments", stats["total_appointments"])
    kpi2.metric("Confirmed Active", stats["confirmed_appointments"])
    kpi3.metric("Cancelled", stats["cancelled_appointments"])
    kpi4.metric("Today's Slots", stats["today_appointments"])
    kpi5.metric("Unique Patients", stats["unique_patients"])
    kpi6.metric("Active Doctors", stats["total_doctors"])

    st.markdown("---")

    # Visual Charts
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("#### 🏥 Appointments by Department")
        if stats["by_specialty"]:
            df_spec = pd.DataFrame(stats["by_specialty"]).set_index("specialty")
            st.bar_chart(df_spec["count"])

    with col_chart2:
        st.markdown("#### 👨‍⚕️ Doctor Workload Distribution")
        if stats["doctor_workload"]:
            df_work = pd.DataFrame(stats["doctor_workload"]).set_index("doctor_name")
            st.bar_chart(df_work["bookings"])

    st.markdown("---")
    st.markdown("#### 📋 Comprehensive Appointments Registry")

    all_appts = st.session_state.db.get_appointments()
    if all_appts:
        table_data = [
            {
                "ID": a.id,
                "Patient": a.patient_name,
                "Doctor": a.doctor_name,
                "Department": a.specialty,
                "Date": a.date,
                "Time Slot": a.time_slot,
                "Status": a.status.value
            }
            for a in all_appts
        ]
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)
