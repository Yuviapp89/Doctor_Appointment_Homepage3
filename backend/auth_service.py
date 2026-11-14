"""
Authentication service for Doctor's Appointment System.
Manages Guest, Patient, and Admin sessions with credential validation.
"""

import uuid
import time
from typing import Optional, Dict, Tuple, Any
from backend.models import Role, User


class AuthService:
    # Standard credentials from specifications
    CREDENTIALS = {
        Role.PATIENT.value: {
            "username": "patient",
            "password": "healthcare",
            "display_name": "Patient John Doe",
            "email": "patient.john@healthcare.org"
        },
        Role.ADMIN.value: {
            "username": "admin",
            "password": "admin",
            "display_name": "Administrator",
            "email": "admin@healthcare.org"
        }
    }

    def __init__(self):
        # Maps session_token -> User
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        role: str = Role.GUEST.value
    ) -> Tuple[bool, Optional[str], Optional[User], str]:
        """
        Validates login parameters and returns (success, token, user, message).
        """
        role = role.lower() if role else Role.GUEST.value

        # 1. Guest Login: No credentials needed
        if role == Role.GUEST.value:
            guest_id = f"guest_{uuid.uuid4().hex[:6]}"
            user = User(
                user_id=guest_id,
                username=guest_id,
                role=Role.GUEST,
                display_name="Guest Visitor",
                email=""
            )
            token = f"token_{uuid.uuid4().hex}"
            self._sessions[token] = {
                "user": user,
                "created_at": time.time()
            }
            return True, token, user, "Logged in as Guest. You can consult our wellness chatbot freely."

        # 2. Patient Login
        elif role == Role.PATIENT.value:
            expected = self.CREDENTIALS[Role.PATIENT.value]
            if not username or not password:
                return False, None, None, "Username and password are required for Patient login."
            
            if username.strip() == expected["username"] and password == expected["password"]:
                user = User(
                    user_id="pat_001",
                    username=expected["username"],
                    role=Role.PATIENT,
                    display_name=expected["display_name"],
                    email=expected["email"]
                )
                token = f"token_{uuid.uuid4().hex}"
                self._sessions[token] = {
                    "user": user,
                    "created_at": time.time()
                }
                return True, token, user, "Welcome back, Patient John Doe! HealthBot is ready to assist your appointment."
            else:
                return False, None, None, "Invalid Patient credentials. Default credentials are username: 'patient' & password: 'healthcare'."

        # 3. Admin Login
        elif role == Role.ADMIN.value:
            expected = self.CREDENTIALS[Role.ADMIN.value]
            if not username or not password:
                return False, None, None, "Username and password are required for Admin login."
            
            if username.strip() == expected["username"] and password == expected["password"]:
                user = User(
                    user_id="adm_001",
                    username=expected["username"],
                    role=Role.ADMIN,
                    display_name=expected["display_name"],
                    email=expected["email"]
                )
                token = f"token_{uuid.uuid4().hex}"
                self._sessions[token] = {
                    "user": user,
                    "created_at": time.time()
                }
                return True, token, user, "Welcome Administrator. Full dashboard and scheduling controls unlocked."
            else:
                return False, None, None, "Invalid Admin credentials. Default credentials are username: 'admin' & password: 'admin'."

        else:
            return False, None, None, f"Unknown role '{role}'. Permitted roles: 'guest', 'patient', 'admin'."

    def validate_token(self, token: Optional[str]) -> Optional[User]:
        """Returns the User object associated with token, or None if invalid."""
        if not token or token not in self._sessions:
            return None
        return self._sessions[token]["user"]

    def logout(self, token: Optional[str]) -> bool:
        """Removes session token."""
        if token and token in self._sessions:
            del self._sessions[token]
            return True
        return False
