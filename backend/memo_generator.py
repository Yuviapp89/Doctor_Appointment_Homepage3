"""
Booking Confirmation Memo Generator.
Generates downloadable, printable, and official appointment confirmation memos.
"""

from typing import Dict, Any
from backend.models import Appointment


class MemoGenerator:
    @staticmethod
    def generate_text_memo(appt: Appointment) -> str:
        """
        Generates a clean, formatted ASCII text memo ready for instant file download.
        """
        divider = "=" * 68
        subdivider = "-" * 68

        memo = f"""
{divider}
       CAREPULSE HEALTHCARE SYSTEM - APPOINTMENT CONFIRMATION MEMO
{divider}

MEMO REFERENCE NO : {appt.id}
ISSUED ON         : {appt.created_at[:19].replace('T', ' ')}
STATUS            : [ {appt.status.value if hasattr(appt.status, 'value') else appt.status} ]

PATIENT DETAILS:
  • Full Name     : {appt.patient_name}
  • Username      : {appt.patient_username}
  • Contact Phone : {appt.patient_contact}

APPOINTMENT SCHEDULE:
  • Doctor Name   : {appt.doctor_name}
  • Department    : {appt.specialty}
  • Date          : {appt.date}
  • Time Slot     : {appt.time_slot}
  • Clinic Venue  : CarePulse Health Tower, Level 3, Suite 304

TRIAGE & CLINICAL NOTES:
  • Symptoms      : {appt.symptoms}
  • Conditions    : {appt.conditions or 'None reported'}

{subdivider}
IMPORTANT PATIENT INSTRUCTIONS:
  1. Please check in at Reception Counter A at least 15 minutes before
     your scheduled slot ({appt.time_slot}).
  2. Bring a valid government-issued photo ID and existing insurance card.
  3. Carry previous medical records, lab reports, or current prescription lists.
  4. If you need to cancel or reschedule, ask HealthBot or contact
     CarePulse Helpdesk at +1 (800) 555-2273.
{subdivider}

VERIFICATION TOKEN: {appt.id}#VERIFIED_OFFICIAL_BOOKING
{divider}
        Thank you for choosing CarePulse Healthcare. Wishing you good health!
{divider}
"""
        return memo.strip()

    @staticmethod
    def generate_html_memo(appt: Appointment) -> str:
        """
        Generates a modern, printable HTML memo with official hospital letterhead styling.
        """
        status_color = "#10b981" if appt.status.value == "CONFIRMED" else "#ef4444"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Booking Confirmation Memo - {appt.id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #f8fafc;
            color: #1e293b;
            margin: 0;
            padding: 24px;
            display: flex;
            justify-content: center;
        }}
        .memo-container {{
            max-width: 700px;
            width: 100%;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 36px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #0284c7;
            padding-bottom: 20px;
            margin-bottom: 24px;
        }}
        .logo-box h1 {{
            margin: 0;
            font-size: 24px;
            color: #0369a1;
            letter-spacing: -0.5px;
        }}
        .logo-box p {{
            margin: 4px 0 0;
            font-size: 13px;
            color: #64748b;
        }}
        .badge-status {{
            background: {status_color};
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .memo-id-row {{
            background: #f1f5f9;
            padding: 12px 16px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            margin-bottom: 24px;
            font-size: 14px;
        }}
        .section-title {{
            font-size: 15px;
            font-weight: 700;
            color: #0f172a;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 6px;
            margin: 20px 0 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            font-size: 14px;
        }}
        .info-item span {{
            display: block;
            color: #64748b;
            font-size: 12px;
            margin-bottom: 2px;
        }}
        .info-item strong {{
            color: #0f172a;
            font-size: 15px;
        }}
        .instructions {{
            background: #f8fafc;
            border-left: 4px solid #0284c7;
            padding: 14px;
            border-radius: 0 8px 8px 0;
            font-size: 13px;
            line-height: 1.5;
            color: #334155;
            margin-top: 24px;
        }}
        .instructions ul {{
            margin: 8px 0 0 18px;
            padding: 0;
        }}
        .footer {{
            margin-top: 32px;
            text-align: center;
            font-size: 12px;
            color: #94a3b8;
            border-top: 1px solid #e2e8f0;
            padding-top: 16px;
        }}
        .print-btn {{
            display: inline-block;
            background: #0284c7;
            color: white;
            text-decoration: none;
            padding: 10px 22px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            margin-top: 16px;
            cursor: pointer;
            border: none;
        }}
        @media print {{
            .print-btn {{ display: none; }}
            body {{ padding: 0; background: white; }}
            .memo-container {{ box-shadow: none; border: none; padding: 10px; }}
        }}
    </style>
</head>
<body>
    <div class="memo-container">
        <div class="header">
            <div class="logo-box">
                <h1>🏥 CarePulse Health Hospital</h1>
                <p>Advanced Clinical Care & Specialty Medical Center</p>
            </div>
            <div>
                <span class="badge-status">{appt.status.value if hasattr(appt.status, 'value') else appt.status}</span>
            </div>
        </div>

        <div class="memo-id-row">
            <div><strong>Appointment Ref:</strong> {appt.id}</div>
            <div><strong>Issue Timestamp:</strong> {appt.created_at[:19].replace('T', ' ')}</div>
        </div>

        <div class="section-title">Patient Profile</div>
        <div class="grid-2">
            <div class="info-item">
                <span>Patient Full Name</span>
                <strong>{appt.patient_name}</strong>
            </div>
            <div class="info-item">
                <span>Registered Account</span>
                <strong>{appt.patient_username}</strong>
            </div>
            <div class="info-item">
                <span>Contact Phone</span>
                <strong>{appt.patient_contact}</strong>
            </div>
            <div class="info-item">
                <span>Clinical Notes</span>
                <strong>{appt.conditions or 'None specified'}</strong>
            </div>
        </div>

        <div class="section-title">Specialist & Appointment Schedule</div>
        <div class="grid-2">
            <div class="info-item">
                <span>Attending Doctor</span>
                <strong>{appt.doctor_name}</strong>
            </div>
            <div class="info-item">
                <span>Department / Specialty</span>
                <strong>{appt.specialty}</strong>
            </div>
            <div class="info-item">
                <span>Scheduled Date</span>
                <strong>{appt.date}</strong>
            </div>
            <div class="info-item">
                <span>Time Slot</span>
                <strong>{appt.time_slot}</strong>
            </div>
        </div>

        <div class="instructions">
            <strong>Check-in & Hospital Guidelines:</strong>
            <ul>
                <li>Please report to Counter 3 at CarePulse Health 15 minutes prior to {appt.time_slot}.</li>
                <li>Present this booking confirmation memo alongside a photo ID at reception.</li>
                <li>Bring past diagnostic evaluations, discharge summaries, or medications currently taken.</li>
                <li>To modify or cancel, consult HealthBot in your patient portal or call (800) 555-CARE.</li>
            </ul>
        </div>

        <div class="footer">
            <p>Verification Code: <code>{appt.id}-AUTH-VERIFIED</code> | CarePulse Digital Medical Record</p>
            <button class="print-btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
        </div>
    </div>
</body>
</html>"""
