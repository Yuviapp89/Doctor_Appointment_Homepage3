"""
Data models for Doctor's Appointment System.
Pure domain models with validation and serialization helpers.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any
import datetime


class Role(str, Enum):
    GUEST = "guest"
    PATIENT = "patient"
    ADMIN = "admin"


class AppointmentStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


@dataclass
class User:
    user_id: str
    username: str
    role: Role
    display_name: str
    email: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role.value if isinstance(self.role, Role) else self.role,
            "display_name": self.display_name,
            "email": self.email
        }


@dataclass
class Doctor:
    id: int
    name: str
    specialty: str
    qualification: str
    experience_years: int
    rating: float
    fee: float
    available_days: List[str]
    available_slots: List[str]
    bio: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Appointment:
    id: str
    patient_username: str
    patient_name: str
    patient_contact: str
    doctor_id: int
    doctor_name: str
    specialty: str
    date: str
    time_slot: str
    symptoms: str
    conditions: str
    status: AppointmentStatus = AppointmentStatus.CONFIRMED
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    cancelled_at: Optional[str] = None
    cancellation_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value if isinstance(self.status, AppointmentStatus) else self.status
        return data


@dataclass
class ChatCard:
    type: str  # "appointment_confirmed", "doctor_card", "stats_summary"
    title: str
    subtitle: str
    details: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChatResponse:
    reply: str
    state: str
    quick_replies: List[str] = field(default_factory=list)
    card: Optional[ChatCard] = None
    download_memo_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "reply": self.reply,
            "state": self.state,
            "quick_replies": self.quick_replies,
            "card": self.card.to_dict() if self.card else None,
            "download_memo_id": self.download_memo_id
        }
        return result
