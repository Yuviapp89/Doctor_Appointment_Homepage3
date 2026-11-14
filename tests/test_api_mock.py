"""
API & Request Handler In-Memory Suite.
Tests APIHandler and HealthcareRequestHandler directly in memory without requiring
network socket binding.
"""

import unittest
import json
import os
import tempfile
from backend.database import Database
from backend.auth_service import AuthService
from backend.chatbot_engine import ChatbotEngine
from backend.api_handler import APIHandler
from backend.models import Role


class TestAPIInMemory(unittest.TestCase):
    def setUp(self):
        self.db = Database(os.path.join(tempfile.gettempdir(), f"test_api_{os.getpid()}.db"))
        self.auth = AuthService()
        self.chatbot = ChatbotEngine(self.db)
        self.api = APIHandler(self.db, self.auth, self.chatbot)

    def test_complete_api_flow(self):
        # 1. Login Guest
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/login",
            query_params={},
            body_data={"role": "guest"},
            headers={}
        )
        self.assertEqual(status, 200)
        guest_res = json.loads(body.decode("utf-8"))
        self.assertTrue(guest_res["success"])
        guest_token = guest_res["token"]

        # 2. Login Patient
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/login",
            query_params={},
            body_data={"username": "patient", "password": "healthcare", "role": "patient"},
            headers={}
        )
        self.assertEqual(status, 200)
        pat_res = json.loads(body.decode("utf-8"))
        self.assertTrue(pat_res["success"])
        patient_token = pat_res["token"]

        # 3. Login Admin
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/login",
            query_params={},
            body_data={"username": "admin", "password": "admin", "role": "admin"},
            headers={}
        )
        self.assertEqual(status, 200)
        adm_res = json.loads(body.decode("utf-8"))
        self.assertTrue(adm_res["success"])
        admin_token = adm_res["token"]

        # 4. Invalid Login
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/login",
            query_params={},
            body_data={"username": "patient", "password": "wrong_password", "role": "patient"},
            headers={}
        )
        self.assertEqual(status, 401)

        # 5. Guest Wellness Query
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/chat",
            query_params={},
            body_data={"message": "How to stay hydrated?", "token": guest_token, "session_id": "s1"},
            headers={}
        )
        self.assertEqual(status, 200)
        chat_res = json.loads(body.decode("utf-8"))
        self.assertIn("Hydration", chat_res["reply"])

        # 6. Guest Prescription Guardrail
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/chat",
            query_params={},
            body_data={"message": "Can you prescribe some antibiotic capsules?", "token": guest_token, "session_id": "s1"},
            headers={}
        )
        self.assertEqual(status, 200)
        guard_res = json.loads(body.decode("utf-8"))
        self.assertIn("Disclaimer", guard_res["reply"])
        self.assertIn("strictly prohibited from prescribing", guard_res["reply"])

        # 7. Patient Multi-turn Triage & Booking
        session_id = "patient_sess_full"
        # Start symptoms triage
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/chat",
            query_params={},
            body_data={"message": "Check symptoms", "token": patient_token, "session_id": session_id},
            headers={}
        )
        self.assertEqual(status, 200)

        # Submit symptoms: rash and eczema
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/chat",
            query_params={},
            body_data={"message": "Itchy red skin rash on arm", "token": patient_token, "session_id": session_id},
            headers={}
        )
        self.assertEqual(status, 200)

        # Submit duration
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/chat",
            query_params={},
            body_data={"message": "3 days", "token": patient_token, "session_id": session_id},
            headers={}
        )
        self.assertEqual(status, 200)

        # Submit conditions -> Recommends Dermatology
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/chat",
            query_params={},
            body_data={"message": "None", "token": patient_token, "session_id": session_id},
            headers={}
        )
        self.assertEqual(status, 200)
        triage_data = json.loads(body.decode("utf-8"))
        self.assertIn("Dermatology", triage_data["reply"])
        self.assertIn("Would you be willing to", triage_data["reply"])

        # Willingness: Yes
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/chat",
            query_params={},
            body_data={"message": "Yes, please book appointment", "token": patient_token, "session_id": session_id},
            headers={}
        )
        self.assertEqual(status, 200)

        # Pick slot
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/chat",
            query_params={},
            body_data={"message": "02:00 PM (Tomorrow)", "token": patient_token, "session_id": session_id},
            headers={}
        )
        self.assertEqual(status, 200)

        # Confirm booking
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/chat",
            query_params={},
            body_data={"message": "Confirm & Generate Memo", "token": patient_token, "session_id": session_id},
            headers={}
        )
        self.assertEqual(status, 200)
        book_res = json.loads(body.decode("utf-8"))
        self.assertIn("officially confirmed", book_res["reply"])
        memo_id = book_res["download_memo_id"]
        self.assertIsNotNone(memo_id)

        # 8. Download Memo
        status, hdrs, memo_bytes = self.api.handle_request(
            method="GET",
            path=f"/api/memo/{memo_id}",
            query_params={"format": "download"},
            body_data=None,
            headers={}
        )
        self.assertEqual(status, 200)
        self.assertIn("attachment", hdrs.get("Content-Disposition", ""))
        self.assertIn("CAREPULSE HEALTHCARE SYSTEM", memo_bytes.decode("utf-8"))

        # 9. HTML Memo
        status, hdrs, html_bytes = self.api.handle_request(
            method="GET",
            path=f"/api/memo/{memo_id}",
            query_params={"format": "html"},
            body_data=None,
            headers={}
        )
        self.assertEqual(status, 200)
        self.assertIn("text/html", hdrs.get("Content-Type", ""))
        self.assertIn(memo_id, html_bytes.decode("utf-8"))

        # 10. Cancellation assistance via chatbot
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/chat",
            query_params={},
            body_data={"message": f"Cancel {memo_id}", "token": patient_token, "session_id": session_id},
            headers={}
        )
        self.assertEqual(status, 200)
        cancel_prompt = json.loads(body.decode("utf-8"))
        self.assertIn("Confirm Appointment Cancellation", cancel_prompt["reply"])

        # Confirm cancel
        status, _, body = self.api.handle_request(
            method="POST",
            path="/api/chat",
            query_params={},
            body_data={"message": f"Yes, Cancel {memo_id}", "token": patient_token, "session_id": session_id},
            headers={}
        )
        self.assertEqual(status, 200)
        cancel_done = json.loads(body.decode("utf-8"))
        self.assertIn("successfully cancelled", cancel_done["reply"])

        # 11. Admin Statistics
        status, _, body = self.api.handle_request(
            method="GET",
            path="/api/stats",
            query_params={"token": admin_token},
            body_data=None,
            headers={}
        )
        self.assertEqual(status, 200)
        stats = json.loads(body.decode("utf-8"))
        self.assertGreaterEqual(stats["total_appointments"], 1)
        self.assertIn("doctor_workload", stats)
        self.assertIn("by_specialty", stats)


if __name__ == "__main__":
    unittest.main()
