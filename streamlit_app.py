"""
CarePulse Health - Streamlit Application Entrypoint.
Displays index.html directly inside Streamlit as a fully functional,
styled, and interactive Doctor's Appointment Web Application.
"""

import os
import sys
import threading

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import streamlit as st
except ImportError:
    st = None

if st is not None:
    # Configure Streamlit page for seamless, full-width display
    st.set_page_config(
        page_title="CarePulse Health - Doctor's Appointment & Virtual Assistant",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Seamless iframe styling: removes default Streamlit paddings and headers
    st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }
        iframe {
            width: 100% !important;
            border: none !important;
        }
    </style>
    """, unsafe_allow_html=True)


def cache_resource_wrapper(func):
    if st is not None and hasattr(st, "cache_resource"):
        return st.cache_resource(func)
    return func


@cache_resource_wrapper
def start_backend_server_daemon():
    """
    Starts the Python backend API server in a background daemon thread
    so that localhost:8000 is active for real-time SQLite persistence.
    """
    try:
        from server import HealthcareRequestHandler
        from http.server import ThreadingHTTPServer
        from backend.database import Database
        from backend.auth_service import AuthService
        from backend.chatbot_engine import ChatbotEngine
        from backend.api_handler import APIHandler

        db = Database()
        auth = AuthService()
        cb = ChatbotEngine(db)
        api = APIHandler(db, auth, cb)
        HealthcareRequestHandler.api_handler = api

        httpd = ThreadingHTTPServer(("127.0.0.1", 8000), HealthcareRequestHandler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        return True
    except Exception as ex:
        # Port 8000 may already be bound or restricted; in-browser engine handles execution seamlessly
        return False


def build_self_contained_html():
    """
    Reads index.html, static/css/styles.css, and static/js/app.js,
    and bundles them into a fully standalone, responsive HTML page
    that functions perfectly inside Streamlit's iframe environment.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    with open(os.path.join(base_dir, "index.html"), "r", encoding="utf-8") as f:
        html = f.read()

    css_path = os.path.join(base_dir, "static", "css", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        html = html.replace(
            '<link rel="stylesheet" href="/static/css/styles.css">',
            f'<style>\n{css}\n</style>'
        )

    js_path = os.path.join(base_dir, "static", "js", "app.js")
    if os.path.exists(js_path):
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()
        html = html.replace(
            '<script src="/static/js/app.js"></script>',
            f'<script>\n{js}\n</script>'
        )

    return html


if st is not None:
    # Start backend thread
    start_backend_server_daemon()

    # Render the complete, functional index.html
    html_page = build_self_contained_html()
    st.components.v1.html(html_page, height=1200, scrolling=True)

    # Helpful sidebar for credentials reference
    with st.sidebar:
        st.markdown("### 🏥 CarePulse Health")
        st.caption("Streamlit Hosted Application")
        st.markdown("---")
        st.markdown("#### 🔑 Login Credentials")
        st.markdown("""
        - **Guest Access:** Click *Continue as Guest* (No credentials required)
        - **Patient Access:** Username: `patient` | Password: `healthcare`
        - **Admin Access:** Username: `admin` | Password: `admin`
        """)
        st.markdown("---")
        st.info("💡 You can interact with the HealthBot directly using the floating robot button in the bottom right corner.")
