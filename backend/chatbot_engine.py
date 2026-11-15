"""
Conversational Chatbot Engine.
Stateful multi-turn dialogue management for Guest, Patient, and Admin modes.
"""

import datetime
from typing import Dict, Any, List, Optional
from backend.models import Role, User, ChatResponse, ChatCard
from backend.database import Database
from backend.triage_engine import TriageEngine


class ChatSession:
    def __init__(self, session_id: str, user: User):
        self.session_id = session_id
        self.user = user
        self.state = "IDLE"
        self.context: Dict[str, Any] = {}
        self.history: List[Dict[str, str]] = []


class ChatbotEngine:
    def __init__(self, db: Database):
        self.db = db
        self.sessions: Dict[str, ChatSession] = {}

    def get_or_create_session(self, session_id: str, user: User) -> ChatSession:
        if session_id not in self.sessions:
            session = ChatSession(session_id, user)
            self.sessions[session_id] = session
            return session
        
        session = self.sessions[session_id]
        # Update user in case role or login status changed
        session.user = user
        return session

    def reset_session(self, session_id: str):
        if session_id in self.sessions:
            user = self.sessions[session_id].user
            self.sessions[session_id] = ChatSession(session_id, user)

    def process_message(self, session_id: str, user: User, user_message: str) -> ChatResponse:
        session = self.get_or_create_session(session_id, user)
        session.history.append({"sender": "user", "text": user_message})

        clean_text = user_message.strip()
        lower_text = clean_text.lower()

        # Handle universal "reset" or "start over"
        if lower_text in ["start over", "reset", "menu", "home"]:
            session.state = "IDLE"
            session.context.clear()
            return self._handle_welcome(session)

        # Route by role
        if user.role == Role.GUEST or user.role == Role.GUEST.value:
            response = self._handle_guest_message(session, clean_text)
        elif user.role == Role.PATIENT or user.role == Role.PATIENT.value:
            response = self._handle_patient_message(session, clean_text)
        elif user.role == Role.ADMIN or user.role == Role.ADMIN.value:
            response = self._handle_admin_message(session, clean_text)
        else:
            response = ChatResponse(
                reply="Unrecognized role. Please refresh the page and log in.",
                state="ERROR",
                quick_replies=["Log In as Patient", "Log In as Admin", "Continue as Guest"]
            )

        session.history.append({"sender": "bot", "text": response.reply})
        return response

    def _handle_welcome(self, session: ChatSession) -> ChatResponse:
        role = session.user.role
        if role == Role.GUEST or role == Role.GUEST.value:
            return ChatResponse(
                reply=(
                    "👋 **Welcome to CarePulse Health!** (Guest Mode)\n\n"
                    "I am your virtual wellness companion. You can ask me for lifestyle, sleep, nutrition, hydration, "
                    "ergonomics, and preventive wellness advice.\n\n"
                    "*(Note: As a guest assistant, I do not prescribe medications. To book specialist appointments, please log in as Patient.)*"
                ),
                state="IDLE",
                quick_replies=[
                    "Tips for better sleep",
                    "Hydration guidelines",
                    "Healthy desk posture",
                    "Stress relief techniques",
                    "Cold prevention tips"
                ]
            )
        elif role == Role.PATIENT or role == Role.PATIENT.value:
            return ChatResponse(
                reply=(
                    f"👋 **Hello {session.user.display_name}!**\n\n"
                    "I am HealthBot, your clinical triage and scheduling assistant. How can I help you today?\n"
                    "• Describe your symptoms to find the right specialist\n"
                    "• Book a doctor's appointment\n"
                    "• Assist with cancelling an existing appointment"
                ),
                state="PATIENT_IDLE",
                quick_replies=[
                    "Check symptoms & book appointment",
                    "My appointments",
                    "Cancel an appointment",
                    "Talk to a Doctor"
                ]
            )
        else:
            return ChatResponse(
                reply=(
                    "🛡️ **Admin Assistant Active**\n\n"
                    "Welcome Administrator. You can ask me to summarize clinic statistics, inspect booked appointments, "
                    "check doctor workloads, or cancel appointments."
                ),
                state="ADMIN_IDLE",
                quick_replies=[
                    "Show system statistics",
                    "List today's appointments",
                    "Doctor workload report",
                    "View all appointments"
                ]
            )

    # =========================================================================
    # GUEST MODE
    # =========================================================================

    def _handle_guest_message(self, session: ChatSession, message: str) -> ChatResponse:
        lower = message.lower()

        # 1. If guest asks to book an appointment directly
        if any(w in lower for w in ["book", "appointment", "schedule", "doctor", "consultation", "see a doctor"]):
            return ChatResponse(
                reply=(
                    "📅 **Booking Appointments:**\n\n"
                    "Direct doctor scheduling and symptom triage require patient identification.\n\n"
                    "Please **Log In as Patient** using the standard credentials:\n"
                    "• **Username:** `patient`\n"
                    "• **Password:** `healthcare`\n\n"
                    "Once logged in, I will evaluate your symptoms, match you with an available specialist, "
                    "book your slot, and issue a downloadable booking confirmation memo!"
                ),
                state="GUEST_INFO",
                quick_replies=[
                    "Log In as Patient",
                    "Tips for better sleep",
                    "Hydration guidelines",
                    "Healthy desk posture",
                    "Stress relief techniques"
                ]
            )

        # 2. Process query via TriageEngine (checks prescriptions, symptoms, or tailored wellness topics)
        reply_text, quick_replies, intent_type = TriageEngine.get_guest_response(message)

        # If symptom details were provided by guest, prompt for patient login
        if intent_type == "symptom_redirect_to_patient":
            return ChatResponse(
                reply=reply_text,
                state="GUEST_SYMPTOM_REDIRECT",
                quick_replies=quick_replies
            )

        return ChatResponse(
            reply=reply_text,
            state="GUEST_CHAT",
            quick_replies=quick_replies
        )

    # =========================================================================
    # PATIENT MODE (TRIAGE -> SPECIALIST MATCH -> BOOKING -> MEMO & CANCEL)
    # =========================================================================

    def _handle_patient_message(self, session: ChatSession, message: str) -> ChatResponse:
        lower = message.lower()

        # Cancellation intent detection at any point
        if any(w in lower for w in ["cancel appointment", "cancel booking", "cancel my appointment", "want to cancel", "cancel an appointment"]) or lower.startswith("cancel "):
            return self._initiate_cancellation_flow(session, message)

        # View existing bookings intent
        if any(w in lower for w in ["my appointments", "my bookings", "show appointments", "view my appointments"]):
            return self._show_patient_appointments(session)

        # State machine dispatch
        state = session.state

        if state == "PATIENT_IDLE" or state == "IDLE":
            if any(w in lower for w in ["symptom", "book", "doctor", "appointment", "check", "sick", "pain", "fever", "rash"]):
                session.state = "AWAITING_SYMPTOMS"
                return ChatResponse(
                    reply=(
                        "🩺 **Step 1 of 3: Clinical Symptoms Assessment**\n\n"
                        "To connect you with the appropriate specialist, please describe:\n"
                        "**What symptoms or discomfort are you experiencing right now?**"
                    ),
                    state="AWAITING_SYMPTOMS",
                    quick_replies=[
                        "Chest pain & heart palpitations",
                        "Skin rash, itching & redness",
                        "Migraine, severe headache & dizziness",
                        "Knee pain & joint stiffness",
                        "High fever, body chills & cough",
                        "Sore throat & sinus congestion"
                    ]
                )
            else:
                return self._handle_welcome(session)

        elif state == "AWAITING_SYMPTOMS":
            session.context["symptoms"] = message
            session.state = "AWAITING_DURATION"
            return ChatResponse(
                reply=(
                    f"📝 Recorded symptoms: *\"{message}\"*\n\n"
                    "⏱️ **Step 2 of 3: Symptom Duration**\n\n"
                    "**How long have you had these symptoms?**"
                ),
                state="AWAITING_DURATION",
                quick_replies=[
                    "Started today",
                    "2 to 3 days",
                    "About a week",
                    "More than two weeks",
                    "Chronic / Several months"
                ]
            )

        elif state == "AWAITING_DURATION":
            session.context["duration"] = message
            session.state = "AWAITING_CONDITIONS"
            return ChatResponse(
                reply=(
                    f"⏱️ Duration noted: *\"{message}\"*\n\n"
                    "📋 **Step 3 of 3: Medical Background**\n\n"
                    "Do you have any **existing medical conditions, chronic illnesses, or drug allergies**?"
                ),
                state="AWAITING_CONDITIONS",
                quick_replies=[
                    "None / Healthy",
                    "Hypertension",
                    "Diabetes (Type 2)",
                    "Asthma",
                    "Penicillin allergy"
                ]
            )

        elif state == "AWAITING_CONDITIONS":
            session.context["conditions"] = message
            symptoms = session.context.get("symptoms", "")
            duration = session.context.get("duration", "")

            # Match specialty
            specialty, rationale = TriageEngine.match_specialty(symptoms)
            session.context["matched_specialty"] = specialty

            session.state = "WILLINGNESS_QUESTION"
            return ChatResponse(
                reply=(
                    f"🔍 **Clinical Assessment Summary:**\n\n"
                    f"• **Symptoms:** {symptoms}\n"
                    f"• **Duration:** {duration}\n"
                    f"• **Medical Conditions:** {message}\n"
                    f"• **Recommended Department:** 🏥 **{specialty}** ({rationale})\n\n"
                    f"Would you be willing to **book an appointment with our {specialty} specialist**?"
                ),
                state="WILLINGNESS_QUESTION",
                quick_replies=[
                    "Yes, please book appointment",
                    "No, not right now"
                ]
            )

        elif state == "WILLINGNESS_QUESTION":
            if any(w in lower for w in ["yes", "yeah", "sure", "book", "please", "ok", "okay"]):
                specialty = session.context.get("matched_specialty", "General Medicine")
                doctors = self.db.get_doctors(specialty)
                if not doctors:
                    doctors = self.db.get_doctors()  # Fallback

                session.context["eligible_doctors"] = [d.to_dict() for d in doctors]
                selected_doc = doctors[0]
                session.context["selected_doctor_id"] = selected_doc.id
                session.context["selected_doctor_name"] = selected_doc.name

                # Target tomorrow's date by default
                tomorrow_date = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
                session.context["target_date"] = tomorrow_date

                # Fetch available slots
                slots = self.db.get_available_slots(selected_doc.id, tomorrow_date)
                if not slots:
                    slots = ["10:00 AM", "02:00 PM", "04:30 PM"]

                session.state = "SELECTING_SLOT"
                slot_buttons = [f"{s} (Tomorrow)" for s in slots[:4]]

                return ChatResponse(
                    reply=(
                        f"Great! I matched you with **{selected_doc.name}** ({selected_doc.specialty}).\n\n"
                        f"• **Qualifications:** {selected_doc.qualification}\n"
                        f"• **Experience:** {selected_doc.experience_years} years (Rating ⭐ {selected_doc.rating})\n"
                        f"• **Consultation Fee:** ${selected_doc.fee:.2f}\n"
                        f"• **Available Date:** {tomorrow_date} (Tomorrow)\n\n"
                        f"Please select your preferred **time slot**:"
                    ),
                    state="SELECTING_SLOT",
                    quick_replies=slot_buttons,
                    card=ChatCard(
                        type="doctor_card",
                        title=selected_doc.name,
                        subtitle=f"{selected_doc.specialty} • ${selected_doc.fee}",
                        details={
                            "Qualification": selected_doc.qualification,
                            "Rating": f"⭐ {selected_doc.rating}/5.0",
                            "Available Date": tomorrow_date
                        }
                    )
                )
            else:
                session.state = "PATIENT_IDLE"
                return ChatResponse(
                    reply=(
                        "No problem at all! Your triage details have been noted.\n\n"
                        "Whenever you're ready to consult a doctor, just ask me anytime. Take care!"
                    ),
                    state="PATIENT_IDLE",
                    quick_replies=[
                        "Check symptoms & book appointment",
                        "My appointments",
                        "Wellness tips"
                    ]
                )

        elif state == "SELECTING_SLOT":
            # Extract time slot from input
            chosen_slot = "10:00 AM"
            for slot_candidate in ["09:00 AM", "10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM", "05:00 PM"]:
                if slot_candidate.lower() in lower:
                    chosen_slot = slot_candidate
                    break
            else:
                # If typed freely, keep first match or candidate
                if "am" in lower or "pm" in lower:
                    chosen_slot = message.split("(")[0].strip()

            session.context["selected_time_slot"] = chosen_slot
            doc_name = session.context.get("selected_doctor_name", "Doctor")
            date_str = session.context.get("target_date", (datetime.date.today() + datetime.timedelta(days=1)).isoformat())

            session.state = "CONFIRM_BOOKING"
            return ChatResponse(
                reply=(
                    f"🗓️ **Review Appointment Details:**\n\n"
                    f"• **Patient Name:** {session.user.display_name}\n"
                    f"• **Specialist:** {doc_name} ({session.context.get('matched_specialty', '')})\n"
                    f"• **Date:** {date_str}\n"
                    f"• **Time:** {chosen_slot}\n"
                    f"• **Venue:** CarePulse Main Health Facility, Suite 304\n\n"
                    f"Would you like me to **confirm this booking and generate your downloadable memo**?"
                ),
                state="CONFIRM_BOOKING",
                quick_replies=[
                    "Confirm & Generate Memo",
                    "Choose different slot",
                    "Cancel"
                ]
            )

        elif state == "CONFIRM_BOOKING":
            if any(w in lower for w in ["confirm", "yes", "generate", "proceed", "book"]):
                # Execute booking in database
                doc_id = session.context.get("selected_doctor_id", 1)
                date_str = session.context.get("target_date", (datetime.date.today() + datetime.timedelta(days=1)).isoformat())
                slot = session.context.get("selected_time_slot", "10:00 AM")
                symptoms = session.context.get("symptoms", "Not specified")
                conditions = session.context.get("conditions", "None")

                success, appt, msg = self.db.book_appointment(
                    patient_username=session.user.username,
                    patient_name=session.user.display_name,
                    patient_contact="+1 (555) 234-5678",
                    doctor_id=doc_id,
                    date=date_str,
                    time_slot=slot,
                    symptoms=symptoms,
                    conditions=conditions
                )

                if not success or not appt:
                    session.state = "PATIENT_IDLE"
                    return ChatResponse(
                        reply=f"❌ Booking failed: {msg}\nPlease choose another slot or try again.",
                        state="PATIENT_IDLE",
                        quick_replies=["Check symptoms & book appointment", "My appointments"]
                    )

                session.state = "PATIENT_IDLE"
                session.context.clear()

                card = ChatCard(
                    type="appointment_confirmed",
                    title=f"Appointment Confirmed: {appt.id}",
                    subtitle=f"{appt.doctor_name} • {appt.specialty}",
                    details={
                        "Appointment ID": appt.id,
                        "Date": appt.date,
                        "Time Slot": appt.time_slot,
                        "Patient": appt.patient_name,
                        "Status": "CONFIRMED ✅"
                    },
                    actions=[
                        {"label": "Download Confirmation Memo", "action": f"download_memo:{appt.id}"},
                        {"label": "Print Memo", "action": f"print_memo:{appt.id}"}
                    ]
                )

                return ChatResponse(
                    reply=(
                        f"🎉 **Your appointment is officially confirmed!**\n\n"
                        f"• **Appointment ID:** `{appt.id}`\n"
                        f"• **Doctor:** {appt.doctor_name} ({appt.specialty})\n"
                        f"• **Scheduled Date:** {appt.date} at {appt.time_slot}\n\n"
                        f"📄 Your **Booking Confirmation Memo** has been generated and is ready to download. "
                        f"You can download it now using the button below!"
                    ),
                    state="PATIENT_IDLE",
                    quick_replies=[
                        "My appointments",
                        "Cancel an appointment",
                        "Book another appointment"
                    ],
                    card=card,
                    download_memo_id=appt.id
                )
            else:
                session.state = "PATIENT_IDLE"
                return ChatResponse(
                    reply="Booking cancelled. You can restart anytime whenever you wish to schedule an appointment.",
                    state="PATIENT_IDLE",
                    quick_replies=["Check symptoms & book appointment", "My appointments"]
                )

        elif state == "SELECTING_CANCELLATION":
            import re
            match = re.search(r"APT-\d{4}-\d+", message.upper())
            if match:
                target_id = match.group(0)
                appt = self.db.get_appointment_by_id(target_id)
                if appt and appt.patient_username == session.user.username and appt.status.value == "CONFIRMED":
                    session.state = "CONFIRM_CANCELLATION"
                    session.context["cancellation_target_id"] = appt.id
                    return ChatResponse(
                        reply=(
                            f"⚠️ **Confirm Appointment Cancellation:**\n\n"
                            f"• **Appointment ID:** `{appt.id}`\n"
                            f"• **Doctor:** {appt.doctor_name} ({appt.specialty})\n"
                            f"• **Scheduled Date:** {appt.date} at {appt.time_slot}\n\n"
                            f"Are you sure you want to cancel this booking?"
                        ),
                        state="CONFIRM_CANCELLATION",
                        quick_replies=[
                            f"Yes, Cancel {appt.id}",
                            "No, Keep Appointment"
                        ]
                    )
            return self._initiate_cancellation_flow(session)

        # Cancellation state
        elif state == "CONFIRM_CANCELLATION":
            target_id = session.context.get("cancellation_target_id")
            if any(w in lower for w in ["yes", "confirm", "proceed", "cancel"]):
                if not target_id:
                    session.state = "PATIENT_IDLE"
                    return ChatResponse(reply="No appointment selected for cancellation.", state="PATIENT_IDLE")

                success, appt, msg = self.db.cancel_appointment(
                    appointment_id=target_id,
                    user_role=session.user.role.value if isinstance(session.user.role, Role) else session.user.role,
                    username=session.user.username,
                    reason="Patient requested cancellation via HealthBot"
                )

                session.state = "PATIENT_IDLE"
                session.context.clear()

                if success:
                    return ChatResponse(
                        reply=(
                            f"✅ **Appointment {target_id} has been successfully cancelled.**\n\n"
                            f"The slot has been released back to our scheduling system. "
                            f"If you'd like to reschedule for a future date, I'm here to help."
                        ),
                        state="PATIENT_IDLE",
                        quick_replies=[
                            "Check symptoms & book appointment",
                            "My appointments",
                            "Wellness tips"
                        ]
                    )
                else:
                    return ChatResponse(
                        reply=f"⚠️ Unable to cancel appointment: {msg}",
                        state="PATIENT_IDLE",
                        quick_replies=["My appointments", "Check symptoms & book appointment"]
                    )
            else:
                session.state = "PATIENT_IDLE"
                session.context.clear()
                return ChatResponse(
                    reply="Appointment cancellation aborted. Your existing appointment remains confirmed and active.",
                    state="PATIENT_IDLE",
                    quick_replies=["My appointments", "Check symptoms & book appointment"]
                )

        # Fallback in patient mode
        return ChatResponse(
            reply=(
                "I am here to assist your clinical scheduling. Would you like to:\n"
                "• **Check symptoms** and book a specialist appointment\n"
                "• **View** your current appointments\n"
                "• **Cancel** an active booking"
            ),
            state="PATIENT_IDLE",
            quick_replies=[
                "Check symptoms & book appointment",
                "My appointments",
                "Cancel an appointment"
            ]
        )

    def _initiate_cancellation_flow(self, session: ChatSession, message: Optional[str] = None) -> ChatResponse:
        # Check if an appointment ID was explicitly provided in message (e.g. "Cancel APT-2026-101")
        if message:
            import re
            match = re.search(r"APT-\d{4}-\d+", message.upper())
            if match:
                target_id = match.group(0)
                appt = self.db.get_appointment_by_id(target_id)
                if not appt:
                    return ChatResponse(
                        reply=f"⚠️ Appointment ID `{target_id}` was not found in our records.",
                        state="PATIENT_IDLE",
                        quick_replies=["My appointments", "Check symptoms & book appointment"]
                    )
                if appt.patient_username != session.user.username:
                    return ChatResponse(
                        reply=f"⚠️ You can only cancel your own appointments.",
                        state="PATIENT_IDLE",
                        quick_replies=["My appointments"]
                    )
                if appt.status.value == "CANCELLED":
                    return ChatResponse(
                        reply=f"ℹ️ Appointment `{target_id}` is already cancelled.",
                        state="PATIENT_IDLE",
                        quick_replies=["My appointments"]
                    )

                session.state = "CONFIRM_CANCELLATION"
                session.context["cancellation_target_id"] = appt.id
                return ChatResponse(
                    reply=(
                        f"⚠️ **Confirm Appointment Cancellation:**\n\n"
                        f"• **Appointment ID:** `{appt.id}`\n"
                        f"• **Doctor:** {appt.doctor_name} ({appt.specialty})\n"
                        f"• **Scheduled Date:** {appt.date} at {appt.time_slot}\n\n"
                        f"Are you sure you want to cancel this booking?"
                    ),
                    state="CONFIRM_CANCELLATION",
                    quick_replies=[
                        f"Yes, Cancel {appt.id}",
                        "No, Keep Appointment"
                    ]
                )

        # Fetch active appointments for this patient
        appts = self.db.get_appointments(
            patient_username=session.user.username,
            status="CONFIRMED"
        )

        if not appts:
            session.state = "PATIENT_IDLE"
            return ChatResponse(
                reply=(
                    "ℹ️ You do not have any active **CONFIRMED** appointments to cancel at this moment.\n\n"
                    "Would you like to book a new appointment?"
                ),
                state="PATIENT_IDLE",
                quick_replies=["Check symptoms & book appointment", "Wellness tips"]
            )

        # If only 1 appointment
        if len(appts) == 1:
            appt = appts[0]
            session.state = "CONFIRM_CANCELLATION"
            session.context["cancellation_target_id"] = appt.id
            return ChatResponse(
                reply=(
                    f"⚠️ **Confirm Appointment Cancellation:**\n\n"
                    f"Found your active appointment:\n"
                    f"• **ID:** `{appt.id}`\n"
                    f"• **Doctor:** {appt.doctor_name} ({appt.specialty})\n"
                    f"• **Date & Time:** {appt.date} at {appt.time_slot}\n\n"
                    f"Are you sure you want to cancel this appointment?"
                ),
                state="CONFIRM_CANCELLATION",
                quick_replies=[
                    f"Yes, Cancel {appt.id}",
                    "No, Keep Appointment"
                ]
            )

        # If multiple appointments
        session.state = "SELECTING_CANCELLATION"
        options = [f"Cancel {a.id}" for a in appts]
        return ChatResponse(
            reply=(
                "📋 You have multiple active appointments. Which one would you like to cancel?\n\n" +
                "\n".join([f"• `{a.id}`: {a.doctor_name} on {a.date} at {a.time_slot}" for a in appts])
            ),
            state="SELECTING_CANCELLATION",
            quick_replies=options
        )

    def _show_patient_appointments(self, session: ChatSession) -> ChatResponse:
        appts = self.db.get_appointments(patient_username=session.user.username)
        if not appts:
            return ChatResponse(
                reply="You haven't booked any appointments yet. Would you like to schedule one?",
                state="PATIENT_IDLE",
                quick_replies=["Check symptoms & book appointment"]
            )

        lines = ["📋 **Your Appointments History:**\n"]
        for a in appts:
            status_emoji = "✅" if a.status.value == "CONFIRMED" else ("❌" if a.status.value == "CANCELLED" else "✓")
            lines.append(
                f"• **{a.id}** ({status_emoji} {a.status.value})\n"
                f"  Doctor: {a.doctor_name} ({a.specialty})\n"
                f"  Schedule: {a.date} at {a.time_slot}\n"
            )

        return ChatResponse(
            reply="\n".join(lines),
            state="PATIENT_IDLE",
            quick_replies=[
                "Check symptoms & book appointment",
                "Cancel an appointment"
            ]
        )

    # =========================================================================
    # ADMIN MODE
    # =========================================================================

    def _handle_admin_message(self, session: ChatSession, message: str) -> ChatResponse:
        lower = message.lower()

        if any(w in lower for w in ["stat", "statistic", "metric", "report", "overview"]):
            stats = self.db.get_statistics()
            reply = (
                f"📊 **System Statistics Overview:**\n\n"
                f"• **Total Appointments:** {stats['total_appointments']}\n"
                f"• **Confirmed (Active):** {stats['confirmed_appointments']}\n"
                f"• **Cancelled:** {stats['cancelled_appointments']}\n"
                f"• **Completed:** {stats['completed_appointments']}\n"
                f"• **Today's Bookings:** {stats['today_appointments']}\n"
                f"• **Unique Patients:** {stats['unique_patients']}\n"
                f"• **Active Specialists:** {stats['total_doctors']}\n\n"
                f"💡 *You can also access the interactive Admin Dashboard in the top menu.*"
            )
            return ChatResponse(
                reply=reply,
                state="ADMIN_IDLE",
                quick_replies=[
                    "List today's appointments",
                    "Doctor workload report",
                    "View all appointments"
                ]
            )

        elif any(w in lower for w in ["today", "today's"]):
            today_str = datetime.date.today().isoformat()
            appts = [a for a in self.db.get_appointments() if a.date == today_str]
            if not appts:
                return ChatResponse(
                    reply=f"No appointments scheduled for today ({today_str}).",
                    state="ADMIN_IDLE",
                    quick_replies=["Show system statistics", "View all appointments"]
                )

            lines = [f"📅 **Appointments for Today ({today_str}):**\n"]
            for a in appts:
                lines.append(f"• `{a.id}` [{a.status.value}] {a.time_slot}: {a.patient_name} with {a.doctor_name} ({a.specialty})")

            return ChatResponse(
                reply="\n".join(lines),
                state="ADMIN_IDLE",
                quick_replies=["Show system statistics", "Doctor workload report"]
            )

        elif any(w in lower for w in ["workload", "doctor workload"]):
            stats = self.db.get_statistics()
            lines = ["👨‍⚕️ **Doctor Workload Distribution:**\n"]
            for item in stats["doctor_workload"]:
                lines.append(f"• **{item['doctor_name']}** ({item['specialty']}): {item['bookings']} bookings")

            return ChatResponse(
                reply="\n".join(lines),
                state="ADMIN_IDLE",
                quick_replies=["Show system statistics", "List today's appointments"]
            )

        elif lower.startswith("cancel "):
            appt_id = clean_text = message.split()[1].upper()
            success, appt, msg = self.db.cancel_appointment(
                appointment_id=appt_id,
                user_role="admin",
                username="admin",
                reason="Admin override cancellation"
            )
            if success:
                return ChatResponse(
                    reply=f"✅ Admin action: Appointment `{appt_id}` has been cancelled.",
                    state="ADMIN_IDLE",
                    quick_replies=["Show system statistics", "View all appointments"]
                )
            else:
                return ChatResponse(
                    reply=f"⚠️ Admin error: {msg}",
                    state="ADMIN_IDLE",
                    quick_replies=["Show system statistics"]
                )

        else:
            return self._handle_welcome(session)
