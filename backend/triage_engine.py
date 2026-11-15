"""
Triage and Wellness Engine.
Handles:
1. Non-prescriptive wellness tips for Guest users tailored specifically to user interest.
2. Clinical symptom detection in Guest mode prompting the user to switch to Patient login.
3. Strict anti-prescription guardrails.
4. Multi-turn symptom analysis and medical specialty recommendation for Patient triage.
"""

import re
from typing import Dict, Any, List, Optional, Tuple


class TriageEngine:
    # Trigger keywords indicating a user is asking for medication or a prescription
    PRESCRIPTION_KEYWORDS = [
        "prescribe", "prescription", "medicine", "medication", "pill", "pills", "tablet", "tablets",
        "antibiotic", "antibiotics", "dosage", "dose", "drug", "drugs", "syrup",
        "capsule", "capsules", "inhaler", "steroid", "steroids", "painkiller", "painkillers",
        "paracetamol", "acetaminophen", "ibuprofen", "amoxicillin", "aspirin", "adderall",
        "xanax", "cure me with medicine", "what medicine", "which pill", "give me pills",
        "recommend medicine", "pharmaceutical", "suggest a drug"
    ]

    _PRESCRIPTION_REGEX = re.compile(
        r"\b(" + "|".join(PRESCRIPTION_KEYWORDS) + r")\b",
        re.IGNORECASE
    )

    # Keywords and phrases indicating clinical symptoms or illness
    SYMPTOM_KEYWORDS = [
        # Pain & aches
        "pain", "hurts", "aching", "ache", "sore", "tender", "throbbing", "stabbing",
        "cramp", "cramps", "stiffness", "swelling", "swollen", "inflamed", "inflammation",
        # Organ systems & parts
        "chest pain", "chest tightness", "palpitation", "palpitations", "racing heart", "heart pain",
        "shortness of breath", "breathless", "difficulty breathing", "wheezing",
        "headache", "migraine", "dizziness", "dizzy", "vertigo", "lightheaded", "faint", "fainting",
        "skin rash", "rash", "itching", "itchy", "red spots", "eczema", "hives", "acne", "blister",
        "knee pain", "back pain", "lower back", "spine pain", "joint pain", "shoulder pain", "neck pain",
        "stomach pain", "stomach ache", "belly ache", "abdominal pain", "nausea", "vomiting", "vomit",
        "diarrhea", "constipation", "acid reflux", "heartburn",
        "throat pain", "sore throat", "cough", "coughing", "ear pain", "earache", "sinus", "runny nose",
        "nasal congestion", "blocked nose", "loss of smell", "loss of taste", "tinnitus",
        "fever", "chills", "high temperature", "shivering", "body ache", "fatigue", "exhaustion",
        "numbness", "tingling", "pins and needles", "seizure", "tremor",
        # Sick statements
        "i am sick", "i feel sick", "feeling unwell", "not feeling well", "having symptoms",
        "contracted", "diagnose me", "what disease", "infection", "infected", "bleeding"
    ]

    _SYMPTOM_REGEX = re.compile(
        r"\b(" + "|".join([re.escape(k) for k in SYMPTOM_KEYWORDS]) + r")\b",
        re.IGNORECASE
    )

    # Curated wellness knowledge base covering diverse health interests
    WELLNESS_TOPICS = {
        "sleep": {
            "keywords": ["sleep", "insomnia", "sleepless", "tired", "wake up", "night", "bedtime", "nap", "circadian", "melatonin", "rest"],
            "title": "Sleep Hygiene & Restorative Sleep",
            "tips": [
                "Aim for 7 to 9 hours of consistent, restorative sleep nightly.",
                "Turn off blue-light emitting screens (phones, monitors) at least 45 minutes before bedtime.",
                "Keep your bedroom cool (around 65°F / 18°C), quiet, and pitch-dark.",
                "Avoid heavy dinners, sugar spikes, or caffeinated drinks within 5-6 hours of bed.",
                "Establish a calming pre-sleep ritual such as light reading, meditation, or warm herbal tea."
            ],
            "related_queries": ["Hydration guidelines", "Stress relief techniques", "Healthy desk posture"]
        },
        "hydration": {
            "keywords": ["water", "hydrate", "hydration", "drink", "drinking", "thirsty", "dehydrated", "electrolytes", "fluids"],
            "title": "Daily Cellular Hydration",
            "tips": [
                "Drink 2.5 to 3 liters (roughly 8-10 glasses) of clean water spread evenly throughout your day.",
                "Begin your morning with 1-2 glasses of room-temperature water to activate metabolism.",
                "Check your hydration status via urine color (pale straw color indicates optimal hydration).",
                "Increase fluid and mineral electrolyte intake during warm weather or vigorous workouts.",
                "Flavor your water naturally with cucumber, fresh lemon, or mint leaves to encourage consistent sipping."
            ],
            "related_queries": ["Nutrition & diet tips", "Energy & morning stamina", "Digestive wellness"]
        },
        "nutrition": {
            "keywords": ["diet", "food", "nutrition", "eat", "eating", "meal", "calories", "protein", "carbs", "sugar", "snack", "weight", "breakfast"],
            "title": "Nutritional Vitality & Balanced Eating",
            "tips": [
                "Adopt the 'Plate Method': 50% colorful vegetables and fruits, 25% lean protein, and 25% whole grains.",
                "Prioritize whole, minimally processed foods over packaged snacks with high sodium or refined oils.",
                "Include healthy omega-3 fats from olive oil, avocados, flaxseeds, and walnuts.",
                "Practice mindful eating: chew slowly, eat without screen distractions, and stop when 80% satisfied.",
                "Incorporate fiber-rich legumes (lentils, chickpeas, black beans) for sustained satiety and blood sugar balance."
            ],
            "related_queries": ["Digestive wellness", "Energy & morning stamina", "Hydration guidelines"]
        },
        "stress": {
            "keywords": ["stress", "anxiety", "anxious", "relax", "relaxation", "calm", "meditation", "breathe", "breathing", "mindfulness", "peace", "burnout", "mental health", "overwhelmed"],
            "title": "Stress Reduction & Mental Equilibrium",
            "tips": [
                "Practice the 4-7-8 breathing method: inhale for 4 seconds, hold for 7 seconds, exhale slowly for 8 seconds.",
                "Take a 10-15 minute mindful outdoor walk in daylight to naturally lower cortisol levels.",
                "Establish firm boundaries with digital work communications after office hours.",
                "Write down 3 things you are grateful for each evening to rewire positive neuro-pathways.",
                "Dedicate 10 minutes daily to meditation or progressive muscle relaxation."
            ],
            "related_queries": ["Sleep hygiene tips", "Healthy desk posture", "Daily physical fitness"]
        },
        "posture": {
            "keywords": ["posture", "back", "neck", "desk", "computer", "chair", "sitting", "ergonomic", "ergonomics", "spine", "standing"],
            "title": "Ergonomics, Posture & Spinal Alignment",
            "tips": [
                "Position your monitor so the top third of the screen is at eye level, roughly an arm's length away.",
                "Apply the 20-20-20 rule: every 20 minutes, gaze at an object 20 feet away for at least 20 seconds.",
                "Maintain your hips, knees, and elbows at roughly 90-degree angles with feet resting flat on the floor.",
                "Use a small lumbar support cushion to preserve the natural inward curve of your lower back.",
                "Stand up, stretch your chest, and roll your shoulders back every 45-60 minutes."
            ],
            "related_queries": ["Joint care & stretching", "Eye health & digital fatigue", "Stress relief techniques"]
        },
        "exercise": {
            "keywords": ["exercise", "workout", "fitness", "gym", "cardio", "run", "running", "walk", "walking", "steps", "strength", "active", "training", "stretching"],
            "title": "Daily Movement & Cardiovascular Fitness",
            "tips": [
                "Aim for at least 150 minutes of moderate aerobic exercise (like brisk walking or cycling) every week.",
                "Incorporate functional resistance training (squats, push-ups, lunges) 2 to 3 days weekly.",
                "Always perform a 5-minute dynamic warm-up before working out and gentle static stretches after.",
                "Break up prolonged sedentary periods by aiming for 7,000 to 10,000 daily steps.",
                "Allow your body adequate rest and recovery days between strenuous exercise sessions."
            ],
            "related_queries": ["Joint care & stretching", "Heart vitality habits", "Energy & morning stamina"]
        },
        "eyes": {
            "keywords": ["eye", "eyes", "eye strain", "vision", "screen", "screens", "blue light", "blurry", "dry eyes", "monitor"],
            "title": "Digital Eye Hygiene & Screen Relief",
            "tips": [
                "Follow the 20-20-20 rule: every 20 minutes, look at an object 20 feet away for 20 seconds.",
                "Blink consciously and frequently—screen usage reduces our natural blink rate by over 50%.",
                "Adjust monitor brightness to match surrounding room illumination and eliminate glare.",
                "Use warm lighting in the evening and enable night/blue-light filter modes on digital devices.",
                "Keep screen distance between 20 to 26 inches away from your face."
            ],
            "related_queries": ["Healthy desk posture", "Sleep hygiene tips", "Stress relief techniques"]
        },
        "digestion": {
            "keywords": ["digestion", "digestive", "gut", "stomach", "bloating", "bloated", "fiber", "probiotic", "metabolism", "bowel", "acid"],
            "title": "Digestive Vitality & Gut Microbiome",
            "tips": [
                "Consume 25 to 35 grams of diverse dietary fiber daily from vegetables, oats, beans, and seeds.",
                "Include naturally fermented foods (plain Greek yogurt, kefir, sauerkraut, kimchi) for probiotic flora.",
                "Chew each bite thoroughly—digestion starts in the mouth with salivary enzymes.",
                "Avoid lying down immediately after meals; wait at least 2 to 3 hours before sleep.",
                "Stay hydrated between meals rather than chugging large amounts of water during eating."
            ],
            "related_queries": ["Hydration guidelines", "Nutrition & diet tips", "Daily physical fitness"]
        },
        "immunity": {
            "keywords": ["immune", "immunity", "cold prevention", "flu", "hygiene", "hands", "illness prevention", "defense", "vitamin c", "vitamin d"],
            "title": "Immune Resilience & Preventative Habits",
            "tips": [
                "Wash hands thoroughly with soap and warm water for at least 20 seconds regularly.",
                "Ensure sufficient dietary intake of Vitamin C (bell peppers, oranges) and Zinc (nuts, seeds).",
                "Get 15-20 minutes of natural sunlight exposure daily to support Vitamin D synthesis.",
                "Prioritize 7-8 hours of sound sleep, as immune antibodies and cytokines are produced during sleep.",
                "Keep chronic stress in check; sustained high cortisol suppresses immune response."
            ],
            "related_queries": ["Sleep hygiene tips", "Hydration guidelines", "Nutrition & diet tips"]
        },
        "energy": {
            "keywords": ["energy", "fatigue", "tired", "slump", "morning", "stamina", "afternoon", "exhausted", "vitality", "routine"],
            "title": "Daily Stamina & Energy Optimization",
            "tips": [
                "Step outside within 30 minutes of waking for natural sunlight to synchronize your circadian clock.",
                "Drink 500ml of room-temperature water first thing in the morning to combat overnight dehydration.",
                "Delay caffeine intake for 60-90 minutes after waking to allow natural adenosine clearance.",
                "Overcome the 2:00 PM afternoon dip with a 10-minute brisk walk and a glass of cold water.",
                "Avoid high-glycemic sugar snacks which cause rapid blood sugar crashes."
            ],
            "related_queries": ["Sleep hygiene tips", "Hydration guidelines", "Daily physical fitness"]
        },
        "heart": {
            "keywords": ["heart", "cardio", "circulation", "artery", "cardiovascular", "blood pressure", "cholesterol", "pulse"],
            "title": "Cardiovascular Health & Heart Vitality",
            "tips": [
                "Engage in daily aerobic movement such as brisk walking, swimming, or cycling.",
                "Limit high-sodium processed foods; season dishes with fresh garlic, herbs, and lemon instead.",
                "Incorporate potassium-rich foods (bananas, spinach, sweet potatoes) to support vascular tone.",
                "Practice deep breathing or meditation to calm sympathetic nervous system blood pressure spikes.",
                "Maintain healthy body composition through balanced portion control and consistent movement."
            ],
            "related_queries": ["Daily physical fitness", "Nutrition & diet tips", "Stress relief techniques"]
        },
        "joints": {
            "keywords": ["joint", "joints", "flexibility", "mobility", "stretch", "stretching", "knee", "spine", "stiff", "yoga", "warmup"],
            "title": "Joint Mobility & Functional Flexibility",
            "tips": [
                "Perform 5-10 minutes of gentle dynamic joint circles (ankles, hips, shoulders) upon waking.",
                "Avoid static sitting for longer than an hour—stand up and do gentle hamstring and hip flexor stretches.",
                "Stay well-hydrated; cartilage and joint synovial fluid depend heavily on water volume.",
                "Incorporate low-impact activities like swimming or cycling that protect joint surfaces.",
                "Wear supportive, cushioned footwear suited to your daily walking surfaces."
            ],
            "related_queries": ["Healthy desk posture", "Daily physical fitness", "Hydration guidelines"]
        }
    }

    # Clinical department mapping for symptom triage
    SPECIALTY_MAPPING = [
        {
            "specialty": "Cardiology",
            "keywords": ["chest pain", "chest tightness", "palpitation", "palpitations", "racing heart", "heart pain", "shortness of breath", "breathless", "high blood pressure", "hypertension", "angina"],
            "description": "Heart rhythm, cardiovascular symptoms, and blood pressure care"
        },
        {
            "specialty": "Dermatology",
            "keywords": ["skin", "rash", "skin rash", "itching", "itchy", "eczema", "acne", "pimple", "red spots", "hives", "psoriasis", "mole", "blister", "boil"],
            "description": "Dermatological evaluation for skin, cutaneous lesions, and rashes"
        },
        {
            "specialty": "Neurology",
            "keywords": ["headache", "migraine", "dizziness", "dizzy", "vertigo", "lightheaded", "numbness", "tingling", "seizure", "tremor", "fainting"],
            "description": "Neurological assessment for brain, nerves, vertigo, and migraines"
        },
        {
            "specialty": "Orthopedics",
            "keywords": ["knee", "joint", "bone", "back pain", "lower back", "spine", "arthritis", "sprain", "fracture", "swollen ankle", "shoulder pain", "hip pain"],
            "description": "Musculoskeletal and orthopedic care for joints, bones, and spine"
        },
        {
            "specialty": "ENT Specialist",
            "keywords": ["ear", "throat", "sore throat", "sinus", "nasal", "nose", "hearing", "tinnitus", "tonsil", "loss of smell", "congestion", "ear pain"],
            "description": "Ear, Nose, and Throat (Otolaryngology) specialist consultation"
        },
        {
            "specialty": "Pediatrics",
            "keywords": ["baby", "child", "infant", "toddler", "pediatric", "kid", "growth", "vaccination", "crying child", "colic"],
            "description": "Pediatric medical care dedicated to infants, children, and teens"
        },
        {
            "specialty": "General Medicine",
            "keywords": ["fever", "cold", "flu", "cough", "fatigue", "weakness", "body ache", "chills", "nausea", "stomach", "vomiting", "diarrhea", "sick", "pain", "unwell"],
            "description": "Comprehensive primary medical evaluation"
        }
    ]

    @classmethod
    def is_prescription_request(cls, text: str) -> bool:
        """Checks if the user text is asking for medication, dosage, or a prescription."""
        return bool(cls._PRESCRIPTION_REGEX.search(text))

    @classmethod
    def has_symptom_details(cls, text: str) -> bool:
        """Checks if the user message describes clinical symptoms, discomfort, or medical issues."""
        clean = text.lower().strip()
        # Direct regex match against clinical symptom indicators
        if cls._SYMPTOM_REGEX.search(clean):
            return True
        # Check against mapped specialty keywords
        for spec in cls.SPECIALTY_MAPPING:
            for kw in spec["keywords"]:
                if kw in clean:
                    return True
        return False

    @classmethod
    def get_guest_response(cls, query: str) -> Tuple[str, List[str], str]:
        """
        Generates a tailored response for Guest users.
        Returns: (reply_text, quick_replies, intent_type)
        Intent types: 'prescription_denied', 'symptom_redirect_to_patient', 'wellness_tip'
        """
        clean_text = query.strip().lower()

        # 1. STRICT GUARDRAIL: Refuse prescription & medication requests
        if cls.is_prescription_request(clean_text):
            reply = (
                "⚠️ **Important Medical Disclaimer & Prescription Policy:**\n\n"
                "As a virtual assistant in **Guest Mode**, I am strictly prohibited from prescribing medications, "
                "recommending pharmaceutical drugs, or calculating dosages.\n\n"
                "🩺 **What you should do:**\n"
                "• For clinical diagnosis, evaluations, and authorized prescriptions, please consult a licensed doctor.\n"
                "• You can **Log In as a Patient** (Credentials: `patient` / `healthcare`) to book an appointment with our specialist physicians!"
            )
            return reply, ["Log In as Patient", "Tips for better sleep", "Healthy desk posture", "Stress relief techniques"], "prescription_denied"

        # 2. SYMPTOM DETECTION: If guest enters clinical symptoms, redirect to Patient login!
        if cls.has_symptom_details(clean_text):
            specialty, rationale = cls.match_specialty(clean_text)
            reply = (
                f"🩺 **Clinical Symptoms Detected:**\n\n"
                f"It sounds like you are experiencing symptoms that require evaluation by our **{specialty}** department ({rationale}).\n\n"
                f"🔒 **Patient Login Required:**\n"
                f"In **Guest Mode**, I can only share general lifestyle and wellness advice. I cannot clinically triage symptoms or confirm appointments without patient verification.\n\n"
                f"👉 **Please Log In with the standard Patient credentials:**\n"
                f"• **Username:** `patient`\n"
                f"• **Password:** `healthcare`\n\n"
                f"Once logged in, I will assess your symptoms in detail, match you with an available specialist, "
                f"book your appointment slot, and issue your official downloadable booking memo!"
            )
            return reply, ["Log In as Patient", "Switch to Patient Mode", "Ask a wellness question instead"], "symptom_redirect_to_patient"

        # 3. TAILORED WELLNESS TIPS: Match user's specific area of interest
        matched_category = None
        best_score = 0

        for cat_key, cat_data in cls.WELLNESS_TOPICS.items():
            score = 0
            for kw in cat_data["keywords"]:
                if kw in clean_text:
                    score += len(kw)  # longer keyword matches get higher weight
            if score > best_score:
                best_score = score
                matched_category = cat_data

        if matched_category:
            tips_formatted = "\n".join([f"• {tip}" for tip in matched_category["tips"]])
            reply = (
                f"🌿 **Wellness Tip: {matched_category['title']}**\n\n"
                f"{tips_formatted}\n\n"
                f"💡 *Remember: These lifestyle suggestions are for vitality and general health. "
                f"If you develop acute symptoms or need clinical treatment, please log in as a Patient to book a doctor consultation.*"
            )
            quick_replies = matched_category.get("related_queries", ["Tips for better sleep", "Hydration guidelines", "Healthy desk posture"])
            return reply, quick_replies, "wellness_tip"

        # 4. Contextual fallback acknowledging user's input topic
        words = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", clean_text) if w not in ["what", "have", "with", "from", "about", "your", "this", "that", "some", "give", "tell", "tips", "help"]]
        topic_mention = f" **{', '.join(words[:2])}**" if words else ""

        reply = (
            f"🌿 **Personalized Wellness Advice{topic_mention}:**\n\n"
            f"Here are foundational wellness practices to support your daily health and vitality:\n\n"
            f"• **Consistent Hydration:** Drink 2.5-3 liters of fresh water daily to boost cellular metabolism.\n"
            f"• **Restorative Sleep:** Maintain 7-9 hours of consistent sleep schedule to support hormonal recovery.\n"
            f"• **Balanced Whole Foods:** Center meals around antioxidant-rich vegetables, lean proteins, and fiber.\n"
            f"• **Daily Physical Movement:** A 30-minute brisk walk daily reduces stress and supports cardiovascular fitness.\n"
            f"• **Ergonomic Breaks:** Stretch your shoulders and back every 45-60 minutes if working at a desk.\n\n"
            f"*(Guest Mode provides non-prescriptive lifestyle tips only. If you are unwell or wish to see a specialist, please log in as a Patient!)*"
        )
        return reply, ["Sleep hygiene tips", "Hydration guidelines", "Stress relief techniques", "Healthy desk posture"], "wellness_tip"

    @classmethod
    def get_guest_wellness_response(cls, query: str) -> str:
        """Helper for backwards compatibility returning reply string directly."""
        reply, _, _ = cls.get_guest_response(query)
        return reply

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
