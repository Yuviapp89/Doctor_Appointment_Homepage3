"""
Triage and Wellness Engine.
Handles:
1. Non-prescriptive wellness tips for Guest users with strict anti-prescription guardrails.
2. Symptom analysis, duration check, and specialty recommendation for Patient triage.
"""

import re
from typing import Dict, Any, List, Optional, Tuple


class TriageEngine:
    # Trigger keywords indicating a user is asking for medication or a prescription
    PRESCRIPTION_KEYWORDS = [
        "prescribe", "prescription", "medicine", "medication", "pill", "tablet",
        "antibiotic", "antibiotics", "dosage", "dose", "drug", "drugs", "syrup",
        "capsule", "inhaler", "steroid", "painkiller", "paracetamol", "acetaminophen",
        "ibuprofen", "amoxicillin", "aspirin", "adderall", "xanax", "cure me with medicine",
        "what medicine", "which pill", "give me pills"
    ]

    # Pre-compiled regex patterns for prescription detection
    _PRESCRIPTION_REGEX = re.compile(
        r"\b(" + "|".join(PRESCRIPTION_KEYWORDS) + r")\b",
        re.IGNORECASE
    )

    # Curated wellness topics and tips for Guest mode
    WELLNESS_KNOWLEDGE = {
        "sleep": {
            "title": "Sleep Hygiene & Restorative Rest",
            "tips": [
                "Aim for 7 to 9 hours of uninterrupted sleep per night.",
                "Maintain a consistent sleep-wake schedule, even on weekends.",
                "Turn off blue-light screens (phones, monitors) at least 45 minutes before bed.",
                "Keep your bedroom cool (around 65°F / 18°C) and dark.",
                "Avoid caffeine or heavy meals within 4-6 hours of your bedtime."
            ]
        },
        "hydration": {
            "title": "Daily Hydration Guidelines",
            "tips": [
                "Drink approximately 2 to 3 liters (8-10 glasses) of fresh water daily.",
                "Start your morning with a glass of warm or room-temperature water.",
                "Increase fluid intake during warm weather or after moderate exercise.",
                "Monitor hydration levels through urine color (pale light-straw yellow indicates good hydration).",
                "Infuse water with lemon, mint, or cucumber slices for refreshing taste."
            ]
        },
        "diet": {
            "title": "Nutritional Vitality & Balanced Eating",
            "tips": [
                "Fill half your plate with colorful vegetables and antioxidant-rich fruits.",
                "Prioritize lean proteins (lentils, fish, poultry, tofu) and whole grains (quinoa, brown rice, oats).",
                "Limit ultra-processed snacks, high-sodium foods, and refined sugars.",
                "Incorporate healthy unsaturated fats from olive oil, avocados, almonds, and flax seeds.",
                "Practice mindful chewing and stop eating when 80% full."
            ]
        },
        "stress": {
            "title": "Stress Reduction & Mental Relaxation",
            "tips": [
                "Practice the 4-7-8 breathing method: inhale for 4s, hold for 7s, exhale slowly for 8s.",
                "Take a 10-minute mindful outdoor walk in natural daylight daily.",
                "Dedicate 15 minutes each evening to journaling or light stretching.",
                "Establish healthy boundaries with work notifications after office hours.",
                "Stay connected with friends, family, or supportive peer groups."
            ]
        },
        "posture": {
            "title": "Ergonomics & Spine Health",
            "tips": [
                "Keep your computer monitor at eye level to prevent neck strain.",
                "Use the 20-20-20 rule: every 20 minutes, look at an object 20 feet away for 20 seconds.",
                "Sit with your feet flat on the floor, hips and knees at roughly 90-degree angles.",
                "Stand up and gently stretch your hamstrings and shoulders every 45-60 minutes.",
                "Use a small lumbar roll or ergonomic cushion to support the lower spine curve."
            ]
        },
        "immunity": {
            "title": "Immune System Support & Preventative Health",
            "tips": [
                "Wash hands thoroughly with soap and water for 20 seconds frequently.",
                "Ensure sufficient dietary intake of Vitamin C (citrus, bell peppers) and Vitamin D.",
                "Engage in at least 150 minutes of moderate aerobic activity weekly.",
                "Stay up-to-date with annual preventative health screenings and immunizations.",
                "Manage chronic stress, as high cortisol levels suppress immune resilience."
            ]
        },
        "exercise": {
            "title": "Daily Physical Movement & Heart Fitness",
            "tips": [
                "Incorporate a 30-minute brisk walk into your daily routine.",
                "Include light strength training (bodyweight squats, resistance bands) 2-3 times weekly.",
                "Always warm up with dynamic stretches before physical activity and cool down after.",
                "Take the stairs instead of the elevator whenever practical.",
                "Listen to your body and allow adequate rest days between intense workouts."
            ]
        }
    }

    # Symptom mapping dictionary for Patient triage
    SPECIALTY_MAPPING = [
        {
            "specialty": "Cardiology",
            "keywords": ["chest pain", "heart", "palpitation", "palpitations", "racing heart", "shortness of breath", "high blood pressure", "hypertension", "angina"],
            "description": "Cardiovascular and heart health evaluation"
        },
        {
            "specialty": "Dermatology",
            "keywords": ["skin", "rash", "itching", "itch", "eczema", "acne", "pimple", "spots", "hives", "psoriasis", "mole", "dry skin", "blister"],
            "description": "Dermatological care for skin, hair, and cutaneous conditions"
        },
        {
            "specialty": "Neurology",
            "keywords": ["headache", "migraine", "dizziness", "vertigo", "numbness", "tingling", "seizure", "memory", "nerve", "tremor", "fainting"],
            "description": "Neurological assessment for brain, nerves, and severe headaches"
        },
        {
            "specialty": "Orthopedics",
            "keywords": ["knee", "joint", "bone", "back pain", "spine", "arthritis", "sprain", "fracture", "swollen ankle", "shoulder pain", "hip pain"],
            "description": "Orthopedic evaluation for bones, joints, muscles, and spine"
        },
        {
            "specialty": "ENT Specialist",
            "keywords": ["ear", "throat", "sore throat", "sinus", "nasal", "nose", "hearing", "tinnitus", "tonsil", "loss of smell", "congestion"],
            "description": "Ear, Nose, and Throat (Otolaryngology) care"
        },
        {
            "specialty": "Pediatrics",
            "keywords": ["baby", "child", "infant", "toddler", "pediatric", "kid", "growth", "vaccination", "crying child"],
            "description": "Pediatric care dedicated to infants, children, and adolescents"
        },
        {
            "specialty": "General Medicine",
            "keywords": ["fever", "cold", "flu", "cough", "fatigue", "weakness", "body ache", "chills", "nausea", "stomach", "vomiting", "diarrhea"],
            "description": "Comprehensive primary medical evaluation"
        }
    ]

    @classmethod
    def is_prescription_request(cls, text: str) -> bool:
        """Checks if the user text is asking for medication, dosage, or a prescription."""
        return bool(cls._PRESCRIPTION_REGEX.search(text))

    @classmethod
    def get_guest_wellness_response(cls, query: str) -> str:
        """
        Generates a non-prescriptive, safe wellness response for Guest users.
        Strictly refuses to prescribe medications.
        """
        clean_text = query.strip().lower()

        # 1. Guardrail against medication/prescription requests
        if cls.is_prescription_request(clean_text):
            return (
                "⚠️ **Important Medical Disclaimer & Prescription Policy:**\n\n"
                "As a wellness virtual assistant in **Guest Mode**, I am strictly prohibited from prescribing medications, "
                "recommending pharmaceutical drugs, or calculating dosages.\n\n"
                "🩺 **What you should do:**\n"
                "• For medical diagnosis, clinical evaluations, and authorized prescriptions, please consult a licensed medical doctor.\n"
                "• You can **Log In as a Patient** (Credentials: `patient` / `healthcare`) to book an appointment with our specialist physicians!"
            )

        # 2. Match wellness topics
        matched_topics = []
        if any(w in clean_text for w in ["sleep", "insomnia", "tired", "wake up", "night", "rest"]):
            matched_topics.append(cls.WELLNESS_KNOWLEDGE["sleep"])
        if any(w in clean_text for w in ["water", "hydrate", "hydration", "drink", "thirsty"]):
            matched_topics.append(cls.WELLNESS_KNOWLEDGE["hydration"])
        if any(w in clean_text for w in ["food", "diet", "nutrition", "eat", "meal", "weight", "sugar"]):
            matched_topics.append(cls.WELLNESS_KNOWLEDGE["diet"])
        if any(w in clean_text for w in ["stress", "anxiety", "relax", "calm", "meditation", "breathe", "peace", "burnout"]):
            matched_topics.append(cls.WELLNESS_KNOWLEDGE["stress"])
        if any(w in clean_text for w in ["posture", "back", "neck", "desk", "computer", "chair", "ergonomic"]):
            matched_topics.append(cls.WELLNESS_KNOWLEDGE["posture"])
        if any(w in clean_text for w in ["immune", "immunity", "cold prevention", "sick", "hygiene", "hands"]):
            matched_topics.append(cls.WELLNESS_KNOWLEDGE["immunity"])
        if any(w in clean_text for w in ["exercise", "workout", "fitness", "run", "walk", "stretch", "steps", "active"]):
            matched_topics.append(cls.WELLNESS_KNOWLEDGE["exercise"])

        # If matching topic found
        if matched_topics:
            topic = matched_topics[0]
            tips_formatted = "\n".join([f"• {tip}" for tip in topic["tips"]])
            return (
                f"🌿 **Wellness Tip: {topic['title']}**\n\n"
                f"{tips_formatted}\n\n"
                f"💡 *Remember: These lifestyle suggestions are for general vitality. If you need clinical advice, please log in as a Patient to book a specialist appointment.*"
            )

        # Fallback general wellness advice
        return (
            "🌿 **General Health & Wellness Guidance:**\n\n"
            "• **Hydration:** Aim for 8-10 glasses of clean water daily to optimize cellular energy.\n"
            "• **Restful Sleep:** 7-9 hours of consistent sleep supports mental clarity and immunity.\n"
            "• **Balanced Nutrition:** Incorporate abundant colorful vegetables, whole grains, and lean proteins.\n"
            "• **Daily Movement:** A brisk 30-minute daily walk substantially improves cardiovascular health.\n"
            "• **Mental Resilience:** Dedicate 5-10 minutes to deep diaphragmatic breathing when experiencing stress.\n\n"
            "*(Note: As a Guest, I provide wellness coaching only and do not prescribe medications. Log in as a Patient to schedule a consultation with our medical doctors!)*"
        )

    @classmethod
    def match_specialty(cls, symptoms: str) -> Tuple[str, str]:
        """
        Analyzes symptoms and returns (specialty, rationale).
        Defaults to General Medicine if no specific organ system is flagged.
        """
        text = symptoms.lower()
        for item in cls.SPECIALTY_MAPPING:
            for kw in item["keywords"]:
                if kw in text:
                    return item["specialty"], item["description"]

        return "General Medicine", "Comprehensive evaluation by a primary care physician"
