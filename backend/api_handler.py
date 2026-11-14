"""
API Handler for Doctor's Appointment System.
Pure JSON REST API router with decoupled services and robust error handling.
"""

import json
import urllib.parse
from typing import Dict, Any, Tuple, Optional
from backend.models import Role, User
from backend.database import Database
from backend.auth_service import AuthService
from backend.chatbot_engine import ChatbotEngine
from backend.memo_generator import MemoGenerator


class APIHandler:
    def __init__(self, db: Database, auth_service: AuthService, chatbot_engine: ChatbotEngine):
        self.db = db
        self.auth_service = auth_service
        self.chatbot_engine = chatbot_engine

    def handle_request(
        self,
        method: str,
        path: str,
        query_params: Dict[str, str],
        body_data: Optional[Dict[str, Any]],
        headers: Dict[str, str]
    ) -> Tuple[int, Dict[str, str], bytes]:
        """
        Dispatches incoming API requests.
        Returns: (status_code, response_headers, response_body_bytes)
        """
        # Default JSON headers
        default_headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }

        if method == "OPTIONS":
            return 204, default_headers, b""

        try:
            # Route: /api/login [POST]
            if path == "/api/login" and method == "POST":
                return self._handle_login(body_data or {}, default_headers)

            # Route: /api/logout [POST]
            elif path == "/api/logout" and method == "POST":
                return self._handle_logout(body_data or {}, default_headers)

            # Route: /api/me [GET]
            elif path == "/api/me" and method == "GET":
                return self._handle_me(query_params, headers, default_headers)

            # Route: /api/chat [POST]
            elif path == "/api/chat" and method == "POST":
                return self._handle_chat(body_data or {}, default_headers)

            # Route: /api/doctors [GET]
            elif path == "/api/doctors" and method == "GET":
                return self._handle_get_doctors(query_params, default_headers)

            # Route: /api/slots [GET]
            elif path == "/api/slots" and method == "GET":
                return self._handle_get_slots(query_params, default_headers)

            # Route: /api/book [POST]
            elif path == "/api/book" and method == "POST":
                return self._handle_book(body_data or {}, default_headers)

            # Route: /api/cancel [POST]
            elif path == "/api/cancel" and method == "POST":
                return self._handle_cancel(body_data or {}, default_headers)

            # Route: /api/appointments [GET]
            elif path == "/api/appointments" and method == "GET":
                return self._handle_get_appointments(query_params, default_headers)

            # Route: /api/stats [GET]
            elif path == "/api/stats" and method == "GET":
                return self._handle_get_stats(query_params, default_headers)

            # Route: /api/memo/<id> [GET]
            elif path.startswith("/api/memo/") and method == "GET":
                appt_id = path.split("/api/memo/")[1].strip()
                return self._handle_memo(appt_id, query_params, default_headers)

            else:
                return 404, default_headers, json.dumps({
                    "error": "API route not found",
                    "path": path,
                    "method": method
                }).encode("utf-8")

        except Exception as ex:
            import traceback
            traceback.print_exc()
            return 500, default_headers, json.dumps({
                "error": "Internal Server Error",
                "details": str(ex)
            }).encode("utf-8")

    # -------------------------------------------------------------------------
    # Route Implementations
    # -------------------------------------------------------------------------

    def _handle_login(self, body: Dict[str, Any], headers: Dict[str, str]) -> Tuple[int, Dict[str, str], bytes]:
        role = body.get("role", "guest")
        username = body.get("username", "")
        password = body.get("password", "")

        success, token, user, message = self.auth_service.login(username, password, role)
        if not success:
            return 401, headers, json.dumps({
                "success": False,
                "error": message
            }).encode("utf-8")

        return 200, headers, json.dumps({
            "success": True,
            "token": token,
            "user": user.to_dict() if user else None,
            "message": message
        }).encode("utf-8")

    def _handle_logout(self, body: Dict[str, Any], headers: Dict[str, str]) -> Tuple[int, Dict[str, str], bytes]:
        token = body.get("token")
        self.auth_service.logout(token)
        return 200, headers, json.dumps({"success": True, "message": "Logged out successfully"}).encode("utf-8")

    def _handle_me(self, query: Dict[str, str], req_headers: Dict[str, str], headers: Dict[str, str]) -> Tuple[int, Dict[str, str], bytes]:
        token = query.get("token") or req_headers.get("Authorization", "").replace("Bearer ", "").strip()
        user = self.auth_service.validate_token(token)
        if not user:
            return 401, headers, json.dumps({"error": "Unauthorized or session expired"}).encode("utf-8")

        return 200, headers, json.dumps({"user": user.to_dict()}).encode("utf-8")

    def _handle_chat(self, body: Dict[str, Any], headers: Dict[str, str]) -> Tuple[int, Dict[str, str], bytes]:
        message = body.get("message", "").strip()
        session_id = body.get("session_id", "default_session")
        token = body.get("token")
        client_role = body.get("role", "guest")

        if not message:
            return 400, headers, json.dumps({"error": "Empty message"}).encode("utf-8")

        # Resolve authenticated user or guest user
        user = self.auth_service.validate_token(token)
        if not user:
            # Fall back to guest role
            user = User(
                user_id="guest_anon",
                username="guest_anon",
                role=Role.GUEST,
                display_name="Guest User"
            )

        chat_response = self.chatbot_engine.process_message(session_id, user, message)
        return 200, headers, json.dumps(chat_response.to_dict()).encode("utf-8")

    def _handle_get_doctors(self, query: Dict[str, str], headers: Dict[str, str]) -> Tuple[int, Dict[str, str], bytes]:
        specialty = query.get("specialty")
        doctors = self.db.get_doctors(specialty)
        return 200, headers, json.dumps({
            "doctors": [d.to_dict() for d in doctors]
        }).encode("utf-8")

    def _handle_get_slots(self, query: Dict[str, str], headers: Dict[str, str]) -> Tuple[int, Dict[str, str], bytes]:
        doc_id_raw = query.get("doctor_id")
        date = query.get("date")

        if not doc_id_raw or not date:
            return 400, headers, json.dumps({"error": "doctor_id and date query parameters are required"}).encode("utf-8")

        try:
            doc_id = int(doc_id_raw)
        except ValueError:
            return 400, headers, json.dumps({"error": "Invalid doctor_id format"}).encode("utf-8")

        slots = self.db.get_available_slots(doc_id, date)
        return 200, headers, json.dumps({
            "doctor_id": doc_id,
            "date": date,
            "available_slots": slots
        }).encode("utf-8")

    def _handle_book(self, body: Dict[str, Any], headers: Dict[str, str]) -> Tuple[int, Dict[str, str], bytes]:
        token = body.get("token")
        user = self.auth_service.validate_token(token)
        if not user or user.role == Role.GUEST:
            return 403, headers, json.dumps({
                "success": False,
                "error": "Booking is restricted to registered patients and admins. Please log in."
            }).encode("utf-8")

        try:
            doctor_id = int(body.get("doctor_id", 0))
            date = body.get("date", "").strip()
            time_slot = body.get("time_slot", "").strip()
            patient_name = body.get("patient_name", user.display_name).strip()
            patient_contact = body.get("patient_contact", "+1 (555) 234-5678").strip()
            symptoms = body.get("symptoms", "General Consultation").strip()
            conditions = body.get("conditions", "None").strip()

            if not doctor_id or not date or not time_slot:
                return 400, headers, json.dumps({"error": "doctor_id, date, and time_slot are required"}).encode("utf-8")

            success, appt, msg = self.db.book_appointment(
                patient_username=user.username,
                patient_name=patient_name,
                patient_contact=patient_contact,
                doctor_id=doctor_id,
                date=date,
                time_slot=time_slot,
                symptoms=symptoms,
                conditions=conditions
            )

            if not success or not appt:
                return 409, headers, json.dumps({"success": False, "error": msg}).encode("utf-8")

            return 201, headers, json.dumps({
                "success": True,
                "appointment": appt.to_dict(),
                "memo_id": appt.id,
                "message": msg
            }).encode("utf-8")

        except Exception as ex:
            return 400, headers, json.dumps({"error": f"Failed to book: {str(ex)}"}).encode("utf-8")

    def _handle_cancel(self, body: Dict[str, Any], headers: Dict[str, str]) -> Tuple[int, Dict[str, str], bytes]:
        token = body.get("token")
        user = self.auth_service.validate_token(token)
        if not user:
            return 401, headers, json.dumps({"error": "Unauthorized"}).encode("utf-8")

        appt_id = body.get("appointment_id", "").strip()
        reason = body.get("reason", "Cancelled by user via portal")

        if not appt_id:
            return 400, headers, json.dumps({"error": "appointment_id is required"}).encode("utf-8")

        success, appt, msg = self.db.cancel_appointment(
            appointment_id=appt_id,
            user_role=user.role.value if isinstance(user.role, Role) else user.role,
            username=user.username,
            reason=reason
        )

        if not success:
            return 400, headers, json.dumps({"success": False, "error": msg}).encode("utf-8")

        return 200, headers, json.dumps({
            "success": True,
            "appointment": appt.to_dict() if appt else None,
            "message": msg
        }).encode("utf-8")

    def _handle_get_appointments(self, query: Dict[str, str], headers: Dict[str, str]) -> Tuple[int, Dict[str, str], bytes]:
        token = query.get("token")
        user = self.auth_service.validate_token(token)
        if not user:
            return 401, headers, json.dumps({"error": "Unauthorized"}).encode("utf-8")

        status_filter = query.get("status")

        if user.role == Role.ADMIN or user.role == Role.ADMIN.value:
            # Admin sees all appointments
            appts = self.db.get_appointments(status=status_filter)
        else:
            # Patient sees only their appointments
            appts = self.db.get_appointments(patient_username=user.username, status=status_filter)

        return 200, headers, json.dumps({
            "appointments": [a.to_dict() for a in appts]
        }).encode("utf-8")

    def _handle_get_stats(self, query: Dict[str, str], headers: Dict[str, str]) -> Tuple[int, Dict[str, str], bytes]:
        token = query.get("token")
        user = self.auth_service.validate_token(token)
        if not user or (user.role != Role.ADMIN and user.role != Role.ADMIN.value):
            return 403, headers, json.dumps({"error": "Forbidden: Admin privileges required"}).encode("utf-8")

        stats = self.db.get_statistics()
        return 200, headers, json.dumps(stats).encode("utf-8")

    def _handle_memo(self, appt_id: str, query: Dict[str, str], headers: Dict[str, str]) -> Tuple[int, Dict[str, str], bytes]:
        appt = self.db.get_appointment_by_id(appt_id)
        if not appt:
            return 404, headers, json.dumps({"error": f"Appointment '{appt_id}' not found"}).encode("utf-8")

        fmt = query.get("format", "download")

        if fmt == "html":
            html_content = MemoGenerator.generate_html_memo(appt)
            html_headers = dict(headers)
            html_headers["Content-Type"] = "text/html; charset=utf-8"
            return 200, html_headers, html_content.encode("utf-8")
        elif fmt == "download":
            text_content = MemoGenerator.generate_text_memo(appt)
            down_headers = dict(headers)
            down_headers["Content-Type"] = "text/plain; charset=utf-8"
            down_headers["Content-Disposition"] = f'attachment; filename="CarePulse-Memo-{appt.id}.txt"'
            return 200, down_headers, text_content.encode("utf-8")
        else:
            return 200, headers, json.dumps({
                "appointment": appt.to_dict(),
                "memo_text": MemoGenerator.generate_text_memo(appt)
            }).encode("utf-8")
