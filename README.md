# CarePulse Health - Doctor Appointment & Virtual Care System

A full-stack, modular doctor's appointment web application featuring an advanced HTML5/CSS3/JavaScript frontend and a Python backend (zero external dependencies, using Python standard library `http.server`, `sqlite3`, `dataclasses`, and `json`).

---

## 🌟 Key Features

### 1. Advanced Homepage UI
- **Semantic HTML5 & Modern CSS3:** Built with accessible `<dialog>`, `<nav>`, `<section>`, `<article>`, `<template>`, flexbox, grid, glassmorphism, and responsive breakpoints.
- **Hero Section:** Action CTAs, interactive clinical triage preview, and stats ribbon.
- **Specialties Grid:** Interactive exploration of 7 clinical departments (Cardiology, Dermatology, Neurology, Orthopedics, General Medicine, Pediatrics, ENT).
- **Doctors Catalog:** Real-time doctor directory with qualifications, experience, ratings, consultation fees, and slot booking.
- **Wellness Hub:** Evidence-based preventative health guidelines (sleep, hydration, ergonomics, stress, diet).

### 2. Multi-Role Authentication System
- **Guest Access:** One-click entry without any credentials required.
- **Patient Access:** Standard credentials:
  - **Username:** `patient`
  - **Password:** `healthcare`
- **Administrator Access:** Standard credentials:
  - **Username:** `admin`
  - **Password:** `admin`
- **Dynamic Role Badge & Navigation:** The UI dynamically adapts tabs and controls based on the logged-in role.

### 3. Intelligent HealthBot Virtual Assistant
- **Guest Mode:**
  - Provides non-prescriptive lifestyle and wellness coaching (sleep hygiene, hydration, desk ergonomics, stress relief, nutrition).
  - **Strict Anti-Prescription Guardrail:** Detects any request for medication, pills, antibiotics, or dosages and strictly refuses with a medical disclaimer, prompting the user to consult a licensed physician or log in as a patient.
- **Patient Mode:**
  - **Multi-Turn Symptom Triage:** Gathers primary symptoms, symptom duration, and existing medical conditions/allergies.
  - **Specialist Matching:** Analyzes clinical presentation and maps to the appropriate medical department.
  - **Willingness Check:** Asks the patient if they are willing to book an appointment with the recommended specialist.
  - **Slot Selection & Booking:** Fetches available doctor slots, verifies slot availability atomically, and confirms the booking.
  - **Downloadable Confirmation Memo:** Generates an official booking confirmation memo downloadable as `.txt` or printable as formatted HTML.
- **Cancellation Assistance:**
  - HealthBot assists in finding and cancelling active appointments by conversational prompt (e.g. *"Cancel appointment"*, *"Cancel APT-2026-101"*).
  - Confirms cancellation before executing to prevent accidental cancellations.
- **Admin Mode:**
  - HealthBot answers natural language queries for live clinic statistics, doctor workloads, and cancellation overrides.

### 4. Admin Dashboard
- **Executive KPIs:** Real-time metric cards for Total Appointments, Confirmed Bookings, Cancelled Bookings, Today's Appointments, Unique Patients, and Doctor Count.
- **Visual Analytics:** CSS/SVG bar charts showing Department distribution and Doctor workload.
- **Interactive Appointments Table:** Live search by patient name or ID, status filtering (Confirmed, Cancelled, Completed), memo download, and admin cancellation controls.

---

## 🏗️ Architecture & Modularity

The project adheres to modular design, separating domain models, data persistence, business logic, and API presentation:

```
├── backend/
│   ├── __init__.py          # Backend package initialization
│   ├── models.py            # Domain dataclasses (User, Doctor, Appointment, ChatResponse)
│   ├── database.py          # SQLite repository with thread-safe connection pooling & migrations
│   ├── auth_service.py      # Session management & credential verification
│   ├── triage_engine.py     # Wellness tips, anti-prescription guardrails & symptom analyzer
│   ├── chatbot_engine.py    # Multi-turn state machine for Guest, Patient, and Admin dialogues
│   ├── memo_generator.py    # Clean downloadable ASCII memo & printable HTML medical slips
│   └── api_handler.py       # REST API dispatcher handling all /api/* routes & error responses
├── static/
│   ├── css/
│   │   └── styles.css       # Responsive CSS3 with custom properties, glassmorphism & animations
│   └── js/
│       └── app.js           # Client-side JavaScript modules (Auth, ChatBot, Catalog, Admin)
├── tests/
│   ├── test_backend.py      # Unit tests for domain models, triage, database & chatbot states
│   └── test_api_mock.py     # In-memory API integration test suite
├── index.html               # Main advanced HTML5 single-page application
├── server.py                # Multi-threaded HTTP server hosting frontend and API
├── streamlit_app.py         # Native Streamlit deployment application
├── requirements.txt         # Dependencies for Streamlit deployment
└── README.md                # Documentation and guide
```

---

## 🚀 How to Run

### Option A: Streamlit Web App (Local or Cloud Deployment)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Launch Streamlit:**
   ```bash
   streamlit run streamlit_app.py
   ```
3. Open the browser at **`http://localhost:8501`**.

---

### Option B: Advanced HTML5 + Python Server

1. **Start the server:**
   ```bash
   python server.py
   ```
2. Open the browser at **`http://localhost:8000/`**.

### Step 3: Run the Test Suites
Run the automated test suites:
```bash
python -m unittest discover tests
```

---

## 🛡️ Error Handling
- **Authentication Errors:** Invalid credentials provide immediate inline error feedback.
- **Booking Conflicts:** Slots already booked cannot be double-booked; slot collision detection ensures ACID consistency.
- **Cancellation Protection:** Validates appointment ownership (patients can only cancel their own appointments; admins can override). Prevents cancelling already cancelled records.
- **Graceful API Fallbacks:** Standard HTTP error codes (400, 401, 403, 404, 409, 500) with detailed JSON error messages.
