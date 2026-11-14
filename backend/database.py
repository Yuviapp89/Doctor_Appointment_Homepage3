"""
Database layer for Doctor's Appointment System.
Thread-safe SQLite storage for Doctors, Appointments, and System Statistics.
"""

import sqlite3
import json
import os
import random
import datetime
from contextlib import contextmanager
from typing import List, Optional, Dict, Any, Tuple
from backend.models import Doctor, Appointment, AppointmentStatus, Role, User


DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "healthcare.db")


class Database:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        """Initializes tables and seeds default data if tables are empty."""
        with self._connection() as conn:
            cursor = conn.cursor()

            # Doctors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS doctors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    specialty TEXT NOT NULL,
                    qualification TEXT NOT NULL,
                    experience_years INTEGER NOT NULL,
                    rating REAL NOT NULL,
                    fee REAL NOT NULL,
                    available_days TEXT NOT NULL, -- JSON array
                    available_slots TEXT NOT NULL, -- JSON array
                    bio TEXT
                )
            """)

            # Appointments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id TEXT PRIMARY KEY,
                    patient_username TEXT NOT NULL,
                    patient_name TEXT NOT NULL,
                    patient_contact TEXT NOT NULL,
                    doctor_id INTEGER NOT NULL,
                    doctor_name TEXT NOT NULL,
                    specialty TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time_slot TEXT NOT NULL,
                    symptoms TEXT NOT NULL,
                    conditions TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'CONFIRMED',
                    created_at TEXT NOT NULL,
                    cancelled_at TEXT,
                    cancellation_reason TEXT,
                    FOREIGN KEY (doctor_id) REFERENCES doctors (id)
                )
            """)

            conn.commit()

            # Seed doctors if empty
            cursor.execute("SELECT COUNT(*) FROM doctors")
            if cursor.fetchone()[0] == 0:
                self._seed_doctors(cursor)
                conn.commit()

            # Seed sample appointments for admin dashboard analytics if empty
            cursor.execute("SELECT COUNT(*) FROM appointments")
            if cursor.fetchone()[0] == 0:
                self._seed_sample_appointments(cursor)
                conn.commit()

    def _seed_doctors(self, cursor: sqlite3.Cursor):
        """Seeds initial realistic doctor profiles across various medical departments."""
        default_days = json.dumps(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
        default_slots = json.dumps([
            "09:00 AM", "10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM", "05:00 PM"
        ])

        doctors_data = [
            (
                "Dr. Sarah Lin", "Cardiology", "MD, FACC - Harvard Medical",
                14, 4.9, 120.0, default_days, default_slots,
                "Cardiovascular specialist focusing on heart wellness, hypertension, and preventive cardiology."
            ),
            (
                "Dr. Marcus Vance", "Dermatology", "MD, FAAD - Johns Hopkins",
                10, 4.8, 95.0, default_days, default_slots,
                "Expert in clinical dermatology, skin rashes, chronic acne, eczema, and dermoscopy."
            ),
            (
                "Dr. Elena Rostova", "Neurology", "MD, PhD - Stanford Medicine",
                16, 4.9, 150.0, default_days, default_slots,
                "Neurological consultant specializing in persistent migraines, vertigo, neuropathic pain, and sleep neurology."
            ),
            (
                "Dr. David Chen", "Orthopedics", "MS, MCh - Mayo Clinic Fellow",
                12, 4.7, 110.0, default_days, default_slots,
                "Orthopedic surgeon dedicated to joint pain, spine health, sports rehabilitation, and arthritis care."
            ),
            (
                "Dr. Aisha Patel", "General Medicine", "MBBS, MD - Oxford Medical",
                15, 4.9, 75.0, default_days, default_slots,
                "Primary care physician addressing acute fevers, respiratory infections, metabolic care, and comprehensive wellness."
            ),
            (
                "Dr. James Wilson", "Pediatrics", "MD, FAAP - Columbia University",
                9, 4.8, 85.0, default_days, default_slots,
                "Compassionate pediatrician treating childhood illnesses, developmental milestones, and adolescent health."
            ),
            (
                "Dr. Sophia Kim", "ENT Specialist", "MS (ENT), DLO - Univ of Michigan",
                11, 4.8, 90.0, default_days, default_slots,
                "Otolaryngology specialist treating chronic sinusitis, throat infections, tinnitus, and inner ear balance."
            ),
        ]

        cursor.executemany("""
            INSERT INTO doctors (
                name, specialty, qualification, experience_years,
                rating, fee, available_days, available_slots, bio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, doctors_data)

    def _seed_sample_appointments(self, cursor: sqlite3.Cursor):
        """Seeds realistic historical and current appointments so Admin dashboard looks rich."""
        today = datetime.date.today().isoformat()
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

        sample_appointments = [
            (
                "APT-2026-101", "patient", "John Doe", "+1 (555) 234-5678",
                1, "Dr. Sarah Lin", "Cardiology", today, "10:00 AM",
                "Mild palpitations after workouts", "None", "CONFIRMED",
                datetime.datetime.now().isoformat(), None, None
            ),
            (
                "APT-2026-102", "alice_smith", "Alice Smith", "+1 (555) 345-6789",
                2, "Dr. Marcus Vance", "Dermatology", today, "02:00 PM",
                "Dry red skin patch on forearm", "Eczema history", "CONFIRMED",
                datetime.datetime.now().isoformat(), None, None
            ),
            (
                "APT-2026-103", "robert_brown", "Robert Brown", "+1 (555) 456-7890",
                4, "Dr. David Chen", "Orthopedics", yesterday, "11:30 AM",
                "Lower back stiffness and knee ache", "Hypertension", "COMPLETED",
                yesterday + "T09:15:00", None, None
            ),
            (
                "APT-2026-104", "clara_oswald", "Clara Oswald", "+1 (555) 567-8901",
                3, "Dr. Elena Rostova", "Neurology", tomorrow, "03:30 PM",
                "Frequent throbbing headaches with photophobia", "Migraine", "CONFIRMED",
                datetime.datetime.now().isoformat(), None, None
            ),
            (
                "APT-2026-105", "patient", "John Doe", "+1 (555) 234-5678",
                5, "Dr. Aisha Patel", "General Medicine", yesterday, "09:00 AM",
                "Seasonal allergy checkup", "Dust allergy", "CANCELLED",
                yesterday + "T08:00:00", yesterday + "T08:30:00", "Schedule conflict"
            ),
            (
                "APT-2026-106", "michael_scott", "Michael Scott", "+1 (555) 678-9012",
                7, "Dr. Sophia Kim", "ENT Specialist", today, "05:00 PM",
                "Persistent sinus headache and nasal blockage", "None", "CONFIRMED",
                datetime.datetime.now().isoformat(), None, None
            ),
        ]

        cursor.executemany("""
            INSERT INTO appointments (
                id, patient_username, patient_name, patient_contact,
                doctor_id, doctor_name, specialty, date, time_slot,
                symptoms, conditions, status, created_at, cancelled_at, cancellation_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_appointments)

    # ------------------ Doctors API ------------------

    def get_doctors(self, specialty: Optional[str] = None) -> List[Doctor]:
        with self._connection() as conn:
            cursor = conn.cursor()
            if specialty:
                cursor.execute("SELECT * FROM doctors WHERE LOWER(specialty) = LOWER(?)", (specialty,))
            else:
                cursor.execute("SELECT * FROM doctors ORDER BY id ASC")

            rows = cursor.fetchall()
            doctors = []
            for row in rows:
                doctors.append(Doctor(
                    id=row["id"],
                    name=row["name"],
                    specialty=row["specialty"],
                    qualification=row["qualification"],
                    experience_years=row["experience_years"],
                    rating=row["rating"],
                    fee=row["fee"],
                    available_days=json.loads(row["available_days"]),
                    available_slots=json.loads(row["available_slots"]),
                    bio=row["bio"] or ""
                ))
            return doctors

    def get_doctor_by_id(self, doctor_id: int) -> Optional[Doctor]:
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Doctor(
                id=row["id"],
                name=row["name"],
                specialty=row["specialty"],
                qualification=row["qualification"],
                experience_years=row["experience_years"],
                rating=row["rating"],
                fee=row["fee"],
                available_days=json.loads(row["available_days"]),
                available_slots=json.loads(row["available_slots"]),
                bio=row["bio"] or ""
            )

    def get_available_slots(self, doctor_id: int, date: str) -> List[str]:
        doctor = self.get_doctor_by_id(doctor_id)
        if not doctor:
            return []

        with self._connection() as conn:
            cursor = conn.cursor()
            # Fetch already booked confirmed slots for this doctor on this date
            cursor.execute("""
                SELECT time_slot FROM appointments
                WHERE doctor_id = ? AND date = ? AND status = 'CONFIRMED'
            """, (doctor_id, date))
            booked_slots = {row["time_slot"] for row in cursor.fetchall()}

        available = [slot for slot in doctor.available_slots if slot not in booked_slots]
        return available

    # ------------------ Appointments API ------------------

    def book_appointment(
        self,
        patient_username: str,
        patient_name: str,
        patient_contact: str,
        doctor_id: int,
        date: str,
        time_slot: str,
        symptoms: str,
        conditions: str
    ) -> Tuple[bool, Optional[Appointment], str]:
        """
        Atomically books an appointment.
        Validates doctor exists, slot is free, and parameters are valid.
        """
        doctor = self.get_doctor_by_id(doctor_id)
        if not doctor:
            return False, None, f"Doctor with ID {doctor_id} not found."

        if not patient_name.strip():
            patient_name = "Patient"
        if not patient_contact.strip():
            patient_contact = "Not provided"

        with self._connection() as conn:
            cursor = conn.cursor()

            # Check for conflict
            cursor.execute("""
                SELECT id FROM appointments
                WHERE doctor_id = ? AND date = ? AND time_slot = ? AND status = 'CONFIRMED'
            """, (doctor_id, date, time_slot))
            existing = cursor.fetchone()
            if existing:
                return False, None, f"Slot {time_slot} on {date} with {doctor.name} is already booked. Please pick another slot."

            # Generate unique appointment ID
            rand_code = random.randint(1000, 9999)
            appt_id = f"APT-2026-{rand_code}"

            now_iso = datetime.datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO appointments (
                    id, patient_username, patient_name, patient_contact,
                    doctor_id, doctor_name, specialty, date, time_slot,
                    symptoms, conditions, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?)
            """, (
                appt_id, patient_username, patient_name, patient_contact,
                doctor.id, doctor.name, doctor.specialty, date, time_slot,
                symptoms, conditions, now_iso
            ))

            appt = Appointment(
                id=appt_id,
                patient_username=patient_username,
                patient_name=patient_name,
                patient_contact=patient_contact,
                doctor_id=doctor.id,
                doctor_name=doctor.name,
                specialty=doctor.specialty,
                date=date,
                time_slot=time_slot,
                symptoms=symptoms,
                conditions=conditions,
                status=AppointmentStatus.CONFIRMED,
                created_at=now_iso
            )
            return True, appt, "Appointment successfully booked!"

    def cancel_appointment(
        self,
        appointment_id: str,
        user_role: str,
        username: str,
        reason: str = "Requested by patient"
    ) -> Tuple[bool, Optional[Appointment], str]:
        """
        Cancels an appointment with permission and status validation.
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
            row = cursor.fetchone()

            if not row:
                return False, None, f"Appointment ID '{appointment_id}' was not found in our records."

            if row["status"] == "CANCELLED":
                return False, None, f"Appointment '{appointment_id}' is already cancelled."

            # Authorization check: Patients can only cancel their own appointments; Admin can cancel any.
            if user_role == Role.PATIENT.value and row["patient_username"] != username:
                return False, None, "Unauthorized: You can only cancel your own appointments."

            now_iso = datetime.datetime.now().isoformat()
            cursor.execute("""
                UPDATE appointments
                SET status = 'CANCELLED', cancelled_at = ?, cancellation_reason = ?
                WHERE id = ?
            """, (now_iso, reason, appointment_id))

            cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
            updated_row = cursor.fetchone()
            appt = self._row_to_appointment(updated_row)
            return True, appt, f"Appointment {appointment_id} has been successfully cancelled."

    def get_appointments(
        self,
        patient_username: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Appointment]:
        with self._connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM appointments WHERE 1=1"
            params = []

            if patient_username:
                query += " AND patient_username = ?"
                params.append(patient_username)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC"
            cursor.execute(query, params)
            return [self._row_to_appointment(row) for row in cursor.fetchall()]

    def get_appointment_by_id(self, appointment_id: str) -> Optional[Appointment]:
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_appointment(row)

    def _row_to_appointment(self, row: sqlite3.Row) -> Appointment:
        return Appointment(
            id=row["id"],
            patient_username=row["patient_username"],
            patient_name=row["patient_name"],
            patient_contact=row["patient_contact"],
            doctor_id=row["doctor_id"],
            doctor_name=row["doctor_name"],
            specialty=row["specialty"],
            date=row["date"],
            time_slot=row["time_slot"],
            symptoms=row["symptoms"],
            conditions=row["conditions"],
            status=AppointmentStatus(row["status"]),
            created_at=row["created_at"],
            cancelled_at=row["cancelled_at"],
            cancellation_reason=row["cancellation_reason"]
        )

    # ------------------ Admin Statistics ------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Calculates comprehensive statistics for the admin dashboard."""
        today = datetime.date.today().isoformat()

        with self._connection() as conn:
            cursor = conn.cursor()

            # Total counts
            cursor.execute("SELECT COUNT(*) FROM appointments")
            total_appointments = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'CONFIRMED'")
            confirmed_appointments = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'CANCELLED'")
            cancelled_appointments = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'COMPLETED'")
            completed_appointments = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM appointments WHERE date = ?", (today,))
            today_appointments = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT patient_username) FROM appointments")
            unique_patients = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM doctors")
            total_doctors = cursor.fetchone()[0]

            # Specialty distribution
            cursor.execute("""
                SELECT specialty, COUNT(*) as count
                FROM appointments
                GROUP BY specialty
                ORDER BY count DESC
            """)
            by_specialty = [{"specialty": row["specialty"], "count": row["count"]} for row in cursor.fetchall()]

            # Doctor workload
            cursor.execute("""
                SELECT doctor_name, specialty, COUNT(*) as bookings
                FROM appointments
                GROUP BY doctor_name, specialty
                ORDER BY bookings DESC
            """)
            doctor_workload = [
                {"doctor_name": row["doctor_name"], "specialty": row["specialty"], "bookings": row["bookings"]}
                for row in cursor.fetchall()
            ]

            return {
                "total_appointments": total_appointments,
                "confirmed_appointments": confirmed_appointments,
                "cancelled_appointments": cancelled_appointments,
                "completed_appointments": completed_appointments,
                "today_appointments": today_appointments,
                "unique_patients": unique_patients,
                "total_doctors": total_doctors,
                "by_specialty": by_specialty,
                "doctor_workload": doctor_workload
            }
