"""
Automated Unit and Integration Tests for Doctor's Appointment Backend.
"""

import unittest
import os
import tempfile
import json
import gc
from backend.database import Database
from backend.auth_service import AuthService
from backend.triage_engine import TriageEngine
from backend.chatbot_engine import ChatbotEngine
from backend.memo_generator import MemoGenerator
from backend.api_handler import APIHandler
from backend.models import Role


class TestBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db_path = os.path.join(tempfile.gettempdir(), f"test_health_{os.getpid()}.db")

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

    def setUp(self):
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except Exception:
                pass

        self.db = Database(db_path=self.test_db_path)
        self.auth = AuthService()
        self.chatbot = ChatbotEngine(self.db)
        self.api = APIHandler(self.db, self.auth, self.chatbot)

    # ------------------ Auth Tests ------------------
    def test_guest_login(self):
        success, token, user, msg = self.auth.login(role="guest")
        self.assertTrue(success)
        self.assertIsNotNone(token)
        self.assertEqual(user.role, Role.GUEST)

    def test_patient_login_success(self):
        success, token, user, msg = self.auth.login(username="patient", password="healthcare", role="patient")
        self.assertTrue(success)
        self.assertEqual(user.role, Role.PATIENT)
        self.assertEqual(user.username, "patient")

    def test_patient_login_failure(self):
        success, token, user, msg = self.auth.login(username="patient", password="wrongpassword", role="patient")
        self.assertFalse(success)
        self.assertIn("Invalid", msg)

    def test_admin_login_success(self):
        success, token, user, msg = self.auth.login(username="admin", password="admin", role="admin")
        self.assertTrue(success)
        self.assertEqual(user.role, Role.ADMIN)

    def test_admin_login_failure(self):
        success, token, user, msg = self.auth.login(username="admin", password="wrongpassword", role="admin")
        self.assertFalse(success)

    # ------------------ Guest Chat & Anti-Prescription Tests ------------------
    def test_guest_wellness_tips(self):
        res = TriageEngine.get_guest_wellness_response("How can I sleep better?")
        self.assertIn("sleep", res.lower())
        self.assertIn("wellness tip", res.lower())

    def test_guest_prescription_guardrail(self):
        prescription_queries = [
            "Can you prescribe me some antibiotics for my sore throat?",
            "What medicine or pills should I take for headache?",
            "Give me a paracetamol dosage for fever",
            "What drug can cure my cough?"
        ]
        for query in prescription_queries:
            res = TriageEngine.get_guest_wellness_response(query)
            self.assertIn("Important Medical Disclaimer", res)
            self.assertIn("strictly prohibited from prescribing", res)

    # ------------------ Patient Triage & Booking Tests ------------------
    def test_patient_triage_flow_and_memo(self):
        _, token, user, _ = self.auth.login(username="patient", password="healthcare", role="patient")
        session_id = "test_sess_01"

        # 1. Ask to book / initiate triage
        resp1 = self.chatbot.process_message(session_id, user, "I want to check symptoms")
        self.assertEqual(resp1.state, "AWAITING_SYMPTOMS")

        # 2. Symptoms input
        resp2 = self.chatbot.process_message(session_id, user, "Severe chest pain and heart palpitations")
        self.assertEqual(resp2.state, "AWAITING_DURATION")

        # 3. Duration input
        resp3 = self.chatbot.process_message(session_id, user, "Started 2 days ago")
        self.assertEqual(resp3.state, "AWAITING_CONDITIONS")

        # 4. Conditions input -> Specialty matching & willingness question
        resp4 = self.chatbot.process_message(session_id, user, "Mild hypertension")
        self.assertEqual(resp4.state, "WILLINGNESS_QUESTION")
        self.assertIn("Cardiology", resp4.reply)
        self.assertIn("Would you be willing to", resp4.reply)

        # 5. Say Yes to willingness question -> Slots displayed
        resp5 = self.chatbot.process_message(session_id, user, "Yes, please book appointment")
        self.assertEqual(resp5.state, "SELECTING_SLOT")
        self.assertIn("Dr. Sarah Lin", resp5.reply)

        # 6. Pick slot -> Review details
        resp6 = self.chatbot.process_message(session_id, user, "10:00 AM (Tomorrow)")
        self.assertEqual(resp6.state, "CONFIRM_BOOKING")
        self.assertIn("Review Appointment Details", resp6.reply)

        # 7. Confirm booking -> Success card + downloadable memo ID
        resp7 = self.chatbot.process_message(session_id, user, "Confirm & Generate Memo")
        self.assertEqual(resp7.state, "PATIENT_IDLE")
        self.assertIsNotNone(resp7.download_memo_id)
        self.assertIn("officially confirmed", resp7.reply)

        # Verify appointment stored in DB
        appt_id = resp7.download_memo_id
        appt = self.db.get_appointment_by_id(appt_id)
        self.assertIsNotNone(appt)
        self.assertEqual(appt.specialty, "Cardiology")
        self.assertEqual(appt.time_slot, "10:00 AM")

        # Test memo generation
        text_memo = MemoGenerator.generate_text_memo(appt)
        self.assertIn("CAREPULSE HEALTHCARE SYSTEM", text_memo)
        self.assertIn(appt_id, text_memo)

        html_memo = MemoGenerator.generate_html_memo(appt)
        self.assertIn("<!DOCTYPE html>", html_memo)
        self.assertIn(appt_id, html_memo)

    # ------------------ Appointment Cancellation Tests ------------------
    def test_cancellation_flow(self):
        _, token, user, _ = self.auth.login(username="patient", password="healthcare", role="patient")
        # Direct book an appointment to cancel
        success, appt, _ = self.db.book_appointment(
            patient_username="patient",
            patient_name="John Doe",
            patient_contact="555-1234",
            doctor_id=1,
            date="2026-11-20",
            time_slot="02:00 PM",
            symptoms="Skin rash",
            conditions="None"
        )
        self.assertTrue(success)

        # Chatbot cancellation flow with explicit appointment ID
        session_id = "test_cancel_sess"
        resp1 = self.chatbot.process_message(session_id, user, f"Cancel {appt.id}")
        self.assertEqual(resp1.state, "CONFIRM_CANCELLATION")

        # Confirm cancellation
        resp2 = self.chatbot.process_message(session_id, user, f"Yes, Cancel {appt.id}")
        self.assertEqual(resp2.state, "PATIENT_IDLE")
        self.assertIn("successfully cancelled", resp2.reply)

        # Verify DB status updated
        updated = self.db.get_appointment_by_id(appt.id)
        self.assertEqual(updated.status.value, "CANCELLED")

        # Verify double cancellation is rejected
        can_cancel_again, _, msg = self.db.cancel_appointment(appt.id, "patient", "patient")
        self.assertFalse(can_cancel_again)
        self.assertIn("already cancelled", msg)

    # ------------------ Admin Dashboard & Statistics Tests ------------------
    def test_admin_dashboard_stats(self):
        stats = self.db.get_statistics()
        self.assertGreaterEqual(stats["total_appointments"], 1)
        self.assertIn("by_specialty", stats)
        self.assertIn("doctor_workload", stats)

    # ------------------ API Endpoints Tests ------------------
    def test_api_login_endpoint(self):
        status, headers, body = self.api.handle_request(
            method="POST",
            path="/api/login",
            query_params={},
            body_data={"username": "patient", "password": "healthcare", "role": "patient"},
            headers={}
        )
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertTrue(data["success"])
        self.assertIn("token", data)

    def test_api_stats_forbidden_for_patient(self):
        _, token, _, _ = self.auth.login(username="patient", password="healthcare", role="patient")
        status, _, body = self.api.handle_request(
            method="GET",
            path="/api/stats",
            query_params={"token": token},
            body_data=None,
            headers={}
        )
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
