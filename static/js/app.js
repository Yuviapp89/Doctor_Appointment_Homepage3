/**
 * CarePulse Healthcare - Modern Modular Client-Side Application
 * Handles Authentication, Real-time Chatbot, Doctor Catalog, Appointments & Admin Dashboard
 */

// ============================================================================
// State Management & Storage
// ============================================================================
const AppState = {
    token: localStorage.getItem("carepulse_token") || null,
    user: JSON.parse(localStorage.getItem("carepulse_user") || "null"),
    role: localStorage.getItem("carepulse_role") || "guest",
    sessionId: localStorage.getItem("carepulse_chat_session") || "session_" + Math.random().toString(36).substring(2, 9),
    doctors: [],
    appointments: [],
    stats: null,

    setSession(token, user, role) {
        this.token = token;
        this.user = user;
        this.role = role;
        localStorage.setItem("carepulse_token", token || "");
        localStorage.setItem("carepulse_user", JSON.stringify(user || null));
        localStorage.setItem("carepulse_role", role || "guest");
    },

    clearSession() {
        this.token = null;
        this.user = null;
        this.role = "guest";
        localStorage.removeItem("carepulse_token");
        localStorage.removeItem("carepulse_user");
        localStorage.removeItem("carepulse_role");
    }
};

// ============================================================================
// Toast Notification Utility
// ============================================================================
const Toast = {
    show(message, type = "primary", duration = 4000) {
        const container = document.getElementById("toastContainer");
        if (!container) return;

        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        
        const icon = type === "success" ? "✅" : (type === "danger" ? "⚠️" : "ℹ️");
        toast.innerHTML = `<span>${icon}</span> <div>${message}</div>`;

        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateX(100%)";
            toast.style.transition = "all 0.3s ease";
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
};

// ============================================================================
// API Client Service & Local Fallback Engine
// ============================================================================
const LocalFallbackEngine = {
    doctors: [
        { id: 1, name: "Dr. Sarah Lin", specialty: "Cardiology", qualification: "MD, FACC - Harvard Medical", experience_years: 14, rating: 4.9, fee: 120.0, bio: "Cardiovascular specialist focusing on heart wellness and hypertension." },
        { id: 2, name: "Dr. Marcus Vance", specialty: "Dermatology", qualification: "MD, FAAD - Johns Hopkins", experience_years: 10, rating: 4.8, fee: 95.0, bio: "Expert in clinical dermatology, skin rashes, and chronic eczema." },
        { id: 3, name: "Dr. Elena Rostova", specialty: "Neurology", qualification: "MD, PhD - Stanford Medicine", experience_years: 16, rating: 4.9, fee: 150.0, bio: "Neurological consultant specializing in persistent migraines and vertigo." },
        { id: 4, name: "Dr. David Chen", specialty: "Orthopedics", qualification: "MS, MCh - Mayo Clinic Fellow", experience_years: 12, rating: 4.7, fee: 110.0, bio: "Orthopedic surgeon dedicated to joint pain and spine health." },
        { id: 5, name: "Dr. Aisha Patel", specialty: "General Medicine", qualification: "MBBS, MD - Oxford Medical", experience_years: 15, rating: 4.9, fee: 75.0, bio: "Primary care physician addressing fevers, infections, and wellness." },
        { id: 6, name: "Dr. James Wilson", specialty: "Pediatrics", qualification: "MD, FAAP - Columbia University", experience_years: 9, rating: 4.8, fee: 85.0, bio: "Compassionate pediatrician treating childhood illnesses." },
        { id: 7, name: "Dr. Sophia Kim", specialty: "ENT Specialist", qualification: "MS (ENT), DLO - Univ of Michigan", experience_years: 11, rating: 4.8, fee: 90.0, bio: "Otolaryngology specialist treating sinusitis, throat, and ear aches." }
    ],

    getStoredAppointments() {
        try {
            const raw = localStorage.getItem("carepulse_mock_appts");
            if (raw) return JSON.parse(raw);
        } catch (_) {}
        const initial = [
            { id: "APT-2026-101", patient_username: "patient", patient_name: "Patient John Doe", patient_contact: "+1 (555) 234-5678", doctor_id: 1, doctor_name: "Dr. Sarah Lin", specialty: "Cardiology", date: "2026-11-20", time_slot: "10:00 AM", symptoms: "Mild palpitations", conditions: "None", status: "CONFIRMED", created_at: new Date().toISOString() },
            { id: "APT-2026-102", patient_username: "alice_smith", patient_name: "Alice Smith", patient_contact: "+1 (555) 345-6789", doctor_id: 2, doctor_name: "Dr. Marcus Vance", specialty: "Dermatology", date: "2026-11-21", time_slot: "02:00 PM", symptoms: "Dry skin patch", conditions: "Eczema", status: "CONFIRMED", created_at: new Date().toISOString() },
            { id: "APT-2026-103", patient_username: "patient", patient_name: "Patient John Doe", patient_contact: "+1 (555) 234-5678", doctor_id: 4, doctor_name: "Dr. David Chen", specialty: "Orthopedics", date: "2026-11-18", time_slot: "11:30 AM", symptoms: "Knee pain", conditions: "None", status: "CANCELLED", created_at: new Date().toISOString() }
        ];
        localStorage.setItem("carepulse_mock_appts", JSON.stringify(initial));
        return initial;
    },

    saveAppointments(list) {
        localStorage.setItem("carepulse_mock_appts", JSON.stringify(list));
    },

    handle(url, options) {
        const path = url.replace(/^http:\/\/[^/]+/, "").split("?")[0];
        const method = (options.method || "GET").toUpperCase();
        const body = options.body ? JSON.parse(options.body) : {};

        // 1. /api/login
        if (path === "/api/login" && method === "POST") {
            const { username, password, role } = body;
            if (role === "guest") {
                return { success: true, token: "mock_guest_token", user: { user_id: "guest_1", role: "guest", display_name: "Guest Visitor" }, message: "Logged in as Guest." };
            }
            if (role === "patient") {
                if (username === "patient" && password === "healthcare") {
                    return { success: true, token: "mock_patient_token", user: { user_id: "pat_001", username: "patient", role: "patient", display_name: "Patient John Doe" }, message: "Welcome back, Patient John Doe!" };
                }
                throw new Error("Invalid Patient credentials. Default credentials: username: 'patient' & password: 'healthcare'");
            }
            if (role === "admin") {
                if (username === "admin" && password === "admin") {
                    return { success: true, token: "mock_admin_token", user: { user_id: "adm_001", username: "admin", role: "admin", display_name: "Administrator" }, message: "Welcome Administrator." };
                }
                throw new Error("Invalid Admin credentials. Default credentials: username: 'admin' & password: 'admin'");
            }
            throw new Error(`Unknown role '${role}'`);
        }

        // 2. /api/doctors
        if (path === "/api/doctors" && method === "GET") {
            return { doctors: this.doctors };
        }

        // 3. /api/appointments
        if (path === "/api/appointments" && method === "GET") {
            const appts = this.getStoredAppointments();
            if (AppState.role === "admin") {
                return { appointments: appts };
            }
            return { appointments: appts.filter(a => a.patient_username === "patient") };
        }

        // 4. /api/cancel
        if (path === "/api/cancel" && method === "POST") {
            const { appointment_id } = body;
            const appts = this.getStoredAppointments();
            const target = appts.find(a => a.id === appointment_id);
            if (!target) throw new Error(`Appointment ${appointment_id} not found.`);
            if (target.status === "CANCELLED") throw new Error(`Appointment ${appointment_id} is already cancelled.`);
            target.status = "CANCELLED";
            this.saveAppointments(appts);
            return { success: true, message: `Appointment ${appointment_id} successfully cancelled.` };
        }

        // 5. /api/stats
        if (path === "/api/stats" && method === "GET") {
            const appts = this.getStoredAppointments();
            return {
                total_appointments: appts.length,
                confirmed_appointments: appts.filter(a => a.status === "CONFIRMED").length,
                cancelled_appointments: appts.filter(a => a.status === "CANCELLED").length,
                completed_appointments: appts.filter(a => a.status === "COMPLETED").length,
                today_appointments: 2,
                unique_patients: 3,
                total_doctors: this.doctors.length,
                by_specialty: [
                    { specialty: "Cardiology", count: 3 },
                    { specialty: "Dermatology", count: 2 },
                    { specialty: "Orthopedics", count: 2 },
                    { specialty: "Neurology", count: 1 }
                ],
                doctor_workload: [
                    { doctor_name: "Dr. Sarah Lin", specialty: "Cardiology", bookings: 3 },
                    { doctor_name: "Dr. Marcus Vance", specialty: "Dermatology", bookings: 2 },
                    { doctor_name: "Dr. David Chen", specialty: "Orthopedics", bookings: 2 }
                ]
            };
        }

        // 6. /api/chat
        if (path === "/api/chat" && method === "POST") {
            const msg = (body.message || "").toLowerCase();
            const role = AppState.role;

            if (role === "guest") {
                if (msg.includes("prescribe") || msg.includes("medicine") || msg.includes("pill") || msg.includes("antibiotic")) {
                    return {
                        reply: "⚠️ **Important Medical Disclaimer & Prescription Policy:**\n\nAs a virtual assistant in **Guest Mode**, I am strictly prohibited from prescribing medications or recommending pharmaceutical drugs.\n\n🩺 Please consult a licensed medical physician or **Log In as a Patient** (Credentials: `patient` / `healthcare`) to book an appointment with our specialists!",
                        state: "GUEST_CHAT",
                        quick_replies: ["Tips for better sleep", "Hydration guidelines", "Healthy desk posture", "Log in as Patient"]
                    };
                }
                return {
                    reply: "🌿 **Wellness Guidance (Guest Mode):**\n\n• Maintain 7-9 hours of consistent sleep.\n• Drink 8-10 glasses of water daily.\n• Take a brisk 30-minute daily walk.\n• Practice 4-7-8 deep breathing to relieve stress.\n\n*(Log in as Patient to consult our specialist doctors!)*",
                    state: "GUEST_CHAT",
                    quick_replies: ["Tips for better sleep", "Hydration guidelines", "Healthy desk posture", "Stress relief techniques"]
                };
            }

            if (role === "patient") {
                if (msg.includes("cancel")) {
                    const appts = this.getStoredAppointments().filter(a => a.patient_username === "patient" && a.status === "CONFIRMED");
                    if (!appts.length) {
                        return { reply: "ℹ️ You do not have any active confirmed appointments to cancel.", state: "PATIENT_IDLE", quick_replies: ["Check symptoms & book appointment"] };
                    }
                    return {
                        reply: `⚠️ Found active appointment: **${appts[0].id}** with ${appts[0].doctor_name} on ${appts[0].date}.\n\nWould you like to cancel it?`,
                        state: "CONFIRM_CANCELLATION",
                        quick_replies: [`Yes, Cancel ${appts[0].id}`, "No, Keep Appointment"]
                    };
                }

                if (msg.includes("yes, cancel")) {
                    const match = body.message.match(/APT-\d{4}-\d+/);
                    if (match) {
                        const targetId = match[0];
                        const appts = this.getStoredAppointments();
                        const found = appts.find(a => a.id === targetId);
                        if (found) found.status = "CANCELLED";
                        this.saveAppointments(appts);
                        return { reply: `✅ Appointment **${targetId}** has been successfully cancelled.`, state: "PATIENT_IDLE", quick_replies: ["My appointments", "Check symptoms & book appointment"] };
                    }
                }

                if (msg.includes("confirm") || msg.includes("generate")) {
                    const randId = "APT-2026-" + Math.floor(1000 + Math.random() * 9000);
                    const newAppt = {
                        id: randId,
                        patient_username: "patient",
                        patient_name: "Patient John Doe",
                        patient_contact: "+1 (555) 234-5678",
                        doctor_id: 1,
                        doctor_name: "Dr. Sarah Lin",
                        specialty: "Cardiology",
                        date: "2026-11-20",
                        time_slot: "10:00 AM",
                        symptoms: "Cardiovascular evaluation",
                        conditions: "None",
                        status: "CONFIRMED",
                        created_at: new Date().toISOString()
                    };
                    const appts = this.getStoredAppointments();
                    appts.unshift(newAppt);
                    this.saveAppointments(appts);
                    return {
                        reply: `🎉 **Your appointment is officially confirmed!**\n\n• **Appointment ID:** \`${randId}\`\n• **Doctor:** Dr. Sarah Lin (Cardiology)\n• **Schedule:** 2026-11-20 at 10:00 AM\n\n📄 Your **Booking Confirmation Memo** has been generated and is ready to download!`,
                        state: "PATIENT_IDLE",
                        download_memo_id: randId,
                        quick_replies: ["My appointments", "Cancel an appointment", "Book another appointment"]
                    };
                }

                if (msg.includes("yes") || msg.includes("sure") || msg.includes("book")) {
                    return {
                        reply: "Great! I matched you with **Dr. Sarah Lin** (Cardiology Specialist).\n\n• **Qualifications:** MD, FACC - Harvard Medical\n• **Experience:** 14 years (⭐ 4.9/5.0)\n• **Available Date:** Tomorrow (2026-11-20)\n\nPlease choose your preferred time slot:",
                        state: "SELECTING_SLOT",
                        quick_replies: ["10:00 AM (Tomorrow)", "02:00 PM (Tomorrow)", "04:30 PM (Tomorrow)"]
                    };
                }

                if (msg.includes("10:00 am") || msg.includes("02:00 pm") || msg.includes("04:30 pm")) {
                    return {
                        reply: "🗓️ **Review Appointment Details:**\n\n• **Patient:** Patient John Doe\n• **Doctor:** Dr. Sarah Lin (Cardiology)\n• **Date:** 2026-11-20\n• **Time Slot:** 10:00 AM\n\nShall I confirm this appointment and generate your downloadable memo?",
                        state: "CONFIRM_BOOKING",
                        quick_replies: ["Confirm & Generate Memo", "Cancel"]
                    };
                }

                // Default triage sequence
                return {
                    reply: "🔍 **Clinical Assessment Summary:**\n\n• **Recommended Department:** 🏥 **Cardiology** (Cardiovascular evaluation)\n\nWould you be willing to **book an appointment with our Cardiology specialist**?",
                    state: "WILLINGNESS_QUESTION",
                    quick_replies: ["Yes, please book appointment", "No, not right now"]
                };
            }

            if (role === "admin") {
                return {
                    reply: "📊 **System Statistics Overview:**\n\n• **Total Appointments:** 6\n• **Confirmed Active:** 4\n• **Cancelled:** 2\n• **Active Specialists:** 7\n\n💡 *Full interactive graphs are available in the Admin Dashboard above.*",
                    state: "ADMIN_IDLE",
                    quick_replies: ["Show system statistics", "List today's appointments", "Doctor workload report"]
                };
            }

            return { reply: "Welcome to CarePulse Health! How can I assist you today?", state: "IDLE" };
        }

        return {};
    }
};

const ApiService = {
    async request(url, options = {}) {
        options.headers = options.headers || {};
        options.headers["Content-Type"] = "application/json";
        if (AppState.token) {
            options.headers["Authorization"] = `Bearer ${AppState.token}`;
        }

        // Auto-detect Python backend host if viewing from a dev server like VS Code Live Server
        let primaryUrl = url;
        if (window.location.protocol.startsWith("http") && window.location.port && window.location.port !== "8000") {
            primaryUrl = `http://${window.location.hostname}:8000${url}`;
        }

        try {
            const response = await fetch(primaryUrl, options);
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                // If static server responded with 405 Method Not Allowed, fallback gracefully to in-browser engine
                if (response.status === 405) {
                    console.warn(`[CarePulse] Endpoint ${url} returned 405 on static server. Activating client-side fallback.`);
                    return LocalFallbackEngine.handle(url, options);
                }
                throw new Error(data.error || `HTTP error ${response.status}`);
            }
            return data;
        } catch (err) {
            // If connection to server.py failed (e.g. server not yet started in terminal), use client-side fallback
            console.warn(`[CarePulse] Network error connecting to ${primaryUrl} (${err.message}). Using local fallback engine.`);
            try {
                return LocalFallbackEngine.handle(url, options);
            } catch (fallbackErr) {
                throw fallbackErr;
            }
        }
    },

    login(username, password, role) {
        return this.request("/api/login", {
            method: "POST",
            body: JSON.stringify({ username, password, role })
        });
    },

    chat(message) {
        return this.request("/api/chat", {
            method: "POST",
            body: JSON.stringify({
                message,
                session_id: AppState.sessionId,
                token: AppState.token,
                role: AppState.role
            })
        });
    },

    getDoctors(specialty = "") {
        const query = specialty ? `?specialty=${encodeURIComponent(specialty)}` : "";
        return this.request(`/api/doctors${query}`);
    },

    getSlots(doctorId, date) {
        return this.request(`/api/slots?doctor_id=${doctorId}&date=${date}`);
    },

    bookAppointment(bookingData) {
        bookingData.token = AppState.token;
        return this.request("/api/book", {
            method: "POST",
            body: JSON.stringify(bookingData)
        });
    },

    cancelAppointment(appointmentId, reason = "Requested by user") {
        return this.request("/api/cancel", {
            method: "POST",
            body: JSON.stringify({
                appointment_id: appointmentId,
                token: AppState.token,
                reason
            })
        });
    },

    getAppointments(status = "") {
        const query = status ? `&status=${status}` : "";
        return this.request(`/api/appointments?token=${AppState.token}${query}`);
    },

    getStats() {
        return this.request(`/api/stats?token=${AppState.token}`);
    }
};

// ============================================================================
// Authentication UI Manager
// ============================================================================
const AuthManager = {
    init() {
        this.loginModal = document.getElementById("loginModal");
        this.loginForm = document.getElementById("loginForm");
        this.roleBadge = document.getElementById("navRoleBadge");
        this.loginBtn = document.getElementById("navLoginBtn");
        this.logoutBtn = document.getElementById("navLogoutBtn");
        this.activeRoleTab = "guest";

        this.bindEvents();
        this.updateNavState();
    },

    bindEvents() {
        // Modal openers
        document.querySelectorAll("[data-open-login]").forEach(btn => {
            btn.addEventListener("click", () => this.openLoginModal(btn.dataset.role || "guest"));
        });

        // Modal closer
        document.getElementById("closeLoginModal")?.addEventListener("click", () => {
            this.loginModal.close();
        });

        // Tab switches
        document.querySelectorAll(".role-tab-btn").forEach(tab => {
            tab.addEventListener("click", (e) => {
                const targetRole = e.target.dataset.roleTab;
                this.switchRoleTab(targetRole);
            });
        });

        // Form submit
        this.loginForm?.addEventListener("submit", async (e) => {
            e.preventDefault();
            await this.handleLoginSubmit();
        });

        // Logout
        this.logoutBtn?.addEventListener("click", () => this.handleLogout());
    },

    openLoginModal(defaultRole = "guest") {
        this.switchRoleTab(defaultRole);
        this.loginModal.showModal();
    },

    switchRoleTab(role) {
        this.activeRoleTab = role;
        document.querySelectorAll(".role-tab-btn").forEach(btn => {
            btn.classList.toggle("active", btn.dataset.roleTab === role);
        });

        const credentialsGroup = document.getElementById("credentialsInputs");
        const hintBox = document.getElementById("credentialsHint");
        const submitBtn = document.getElementById("loginSubmitBtn");
        const usernameInput = document.getElementById("loginUsername");
        const passwordInput = document.getElementById("loginPassword");

        if (role === "guest") {
            credentialsGroup.style.display = "none";
            hintBox.innerHTML = "✨ <strong>Guest Access:</strong> No username or password required. Instantly explore wellness advice!";
            submitBtn.textContent = "Continue as Guest";
            usernameInput.removeAttribute("required");
            passwordInput.removeAttribute("required");
        } else if (role === "patient") {
            credentialsGroup.style.display = "block";
            hintBox.innerHTML = "🔑 <strong>Default Patient Credentials:</strong> Username: <code>patient</code> & Password: <code>healthcare</code>";
            submitBtn.textContent = "Log In as Patient";
            usernameInput.setAttribute("required", "required");
            passwordInput.setAttribute("required", "required");
            usernameInput.value = "patient";
            passwordInput.value = "healthcare";
        } else if (role === "admin") {
            credentialsGroup.style.display = "block";
            hintBox.innerHTML = "🛡️ <strong>Default Admin Credentials:</strong> Username: <code>admin</code> & Password: <code>admin</code>";
            submitBtn.textContent = "Log In as Administrator";
            usernameInput.setAttribute("required", "required");
            passwordInput.setAttribute("required", "required");
            usernameInput.value = "admin";
            passwordInput.value = "admin";
        }
    },

    async handleLoginSubmit() {
        const username = document.getElementById("loginUsername").value.trim();
        const password = document.getElementById("loginPassword").value.trim();
        const errorAlert = document.getElementById("loginErrorAlert");
        errorAlert.style.display = "none";

        try {
            const res = await ApiService.login(username, password, this.activeRoleTab);
            AppState.setSession(res.token, res.user, res.user.role);
            this.loginModal.close();
            this.updateNavState();
            Toast.show(res.message, "success");

            // Update chatbot context
            ChatBot.updateHeaderForRole();
            ChatBot.sendBotMessage(`👋 Switched to **${res.user.display_name}** (${res.user.role.toUpperCase()} Mode).`);

            // Refresh appointments or admin dashboard
            if (res.user.role === "patient") {
                AppointmentsManager.loadPatientAppointments();
            } else if (res.user.role === "admin") {
                AdminDashboard.loadDashboard();
            }
        } catch (err) {
            errorAlert.textContent = err.message || "Login failed. Please check your credentials.";
            errorAlert.style.display = "block";
        }
    },

    handleLogout() {
        AppState.clearSession();
        this.updateNavState();
        Toast.show("Logged out. Continuing in Guest Mode.", "primary");
        ChatBot.updateHeaderForRole();
        ChatBot.resetChat();

        // Switch visible sections
        document.getElementById("patientAppointmentsSection").style.display = "none";
        document.getElementById("adminDashboardSection").style.display = "none";
    },

    updateNavState() {
        const role = AppState.role;
        const user = AppState.user;

        // Role badge styling
        this.roleBadge.className = `role-badge badge-${role}`;
        if (role === "patient") {
            this.roleBadge.innerHTML = `🩺 Patient: ${user?.display_name || "John Doe"}`;
        } else if (role === "admin") {
            this.roleBadge.innerHTML = `🛡️ Admin: ${user?.display_name || "System"}`;
        } else {
            this.roleBadge.innerHTML = `👤 Guest Mode`;
        }

        // Toggle buttons
        if (role === "guest") {
            this.loginBtn.style.display = "inline-flex";
            this.logoutBtn.style.display = "none";
            document.getElementById("navMyAppointments").style.display = "none";
            document.getElementById("navAdminDashboard").style.display = "none";
            document.getElementById("patientAppointmentsSection").style.display = "none";
            document.getElementById("adminDashboardSection").style.display = "none";
        } else if (role === "patient") {
            this.loginBtn.style.display = "none";
            this.logoutBtn.style.display = "inline-flex";
            document.getElementById("navMyAppointments").style.display = "inline-block";
            document.getElementById("navAdminDashboard").style.display = "none";
            document.getElementById("patientAppointmentsSection").style.display = "block";
            document.getElementById("adminDashboardSection").style.display = "none";
            AppointmentsManager.loadPatientAppointments();
        } else if (role === "admin") {
            this.loginBtn.style.display = "none";
            this.logoutBtn.style.display = "inline-flex";
            document.getElementById("navMyAppointments").style.display = "inline-block";
            document.getElementById("navAdminDashboard").style.display = "inline-block";
            document.getElementById("patientAppointmentsSection").style.display = "none";
            document.getElementById("adminDashboardSection").style.display = "block";
            AdminDashboard.loadDashboard();
        }
    }
};

// ============================================================================
// Interactive Chatbot Engine
// ============================================================================
const ChatBot = {
    init() {
        this.launcher = document.getElementById("chatbotLauncher");
        this.window = document.getElementById("chatbotWindow");
        this.closeBtn = document.getElementById("closeChatBtn");
        this.minimizeBtn = document.getElementById("minimizeChatBtn");
        this.resetBtn = document.getElementById("resetChatBtn");
        this.messagesContainer = document.getElementById("chatMessages");
        this.quickRepliesContainer = document.getElementById("quickRepliesContainer");
        this.input = document.getElementById("chatInput");
        this.sendBtn = document.getElementById("chatSendBtn");
        this.roleIndicator = document.getElementById("chatRoleIndicator");
        this.roleBanner = document.getElementById("chatRoleBanner");

        this.bindEvents();
        this.updateHeaderForRole();

        // Send initial greeting if empty
        if (this.messagesContainer.children.length === 0) {
            this.requestBotWelcome();
        }
    },

    bindEvents() {
        this.launcher?.addEventListener("click", () => this.toggleWindow());
        this.closeBtn?.addEventListener("click", () => this.closeWindow());
        this.minimizeBtn?.addEventListener("click", () => this.closeWindow());
        this.resetBtn?.addEventListener("click", () => this.resetChat());

        // External openers (e.g., Hero CTAs or quick prompts)
        document.querySelectorAll("[data-open-chat]").forEach(btn => {
            btn.addEventListener("click", () => {
                this.openWindow();
                const prompt = btn.dataset.prompt;
                if (prompt) {
                    this.sendUserMessage(prompt);
                }
            });
        });

        // Send input
        this.sendBtn?.addEventListener("click", () => this.handleSendMessage());
        this.input?.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });
    },

    toggleWindow() {
        if (this.window.classList.contains("hidden")) {
            this.openWindow();
        } else {
            this.closeWindow();
        }
    },

    openWindow() {
        this.window.classList.remove("hidden");
        this.input.focus();
        this.scrollToBottom();
    },

    closeWindow() {
        this.window.classList.add("hidden");
    },

    updateHeaderForRole() {
        const role = AppState.role;
        this.roleIndicator.textContent = `${role} mode`;

        if (role === "guest") {
            this.roleBanner.innerHTML = "🌿 <span><strong>Wellness Mode:</strong> Lifestyle advice only. No prescriptions issued.</span>";
        } else if (role === "patient") {
            this.roleBanner.innerHTML = "🩺 <span><strong>Patient Triage:</strong> Symptom check & specialist booking enabled.</span>";
        } else if (role === "admin") {
            this.roleBanner.innerHTML = "🛡️ <span><strong>Admin Controls:</strong> Clinic overview, stats & schedule oversight.</span>";
        }
    },

    async requestBotWelcome() {
        try {
            const res = await ApiService.chat("start over");
            this.renderBotResponse(res);
        } catch (err) {
            this.sendBotMessage("👋 Hello! Welcome to CarePulse Health. How can I assist you today?");
        }
    },

    async resetChat() {
        this.messagesContainer.innerHTML = "";
        this.quickRepliesContainer.innerHTML = "";
        await this.requestBotWelcome();
        Toast.show("Chat session refreshed.", "primary");
    },

    async handleSendMessage() {
        const text = this.input.value.trim();
        if (!text) return;

        this.input.value = "";
        await this.sendUserMessage(text);
    },

    async sendUserMessage(text) {
        this.appendMessage(text, "user");
        this.quickRepliesContainer.innerHTML = ""; // Clear existing pills

        // Show typing indicator
        const typingEl = this.showTypingIndicator();

        try {
            const data = await ApiService.chat(text);
            typingEl.remove();
            this.renderBotResponse(data);
        } catch (err) {
            typingEl.remove();
            this.sendBotMessage("⚠️ Sorry, I encountered an error communicating with the clinic server. Please try again.");
        }
    },

    sendBotMessage(text) {
        this.appendMessage(text, "bot");
    },

    renderBotResponse(data) {
        this.appendMessage(data.reply, "bot");

        // Render embedded rich card if present
        if (data.card) {
            this.renderCard(data.card);
        }

        // Render download memo button if memo ID generated
        if (data.download_memo_id) {
            this.renderDownloadMemoBox(data.download_memo_id);
            // Also refresh patient appointments list in the background
            if (AppState.role === "patient") {
                AppointmentsManager.loadPatientAppointments();
            }
        }

        // Render quick reply chips
        if (data.quick_replies && data.quick_replies.length > 0) {
            this.renderQuickReplies(data.quick_replies);
        }

        this.scrollToBottom();
    },

    appendMessage(text, sender) {
        const row = document.createElement("div");
        row.className = `message-row ${sender}-row`;

        const avatar = document.createElement("div");
        avatar.className = `msg-avatar ${sender}-avatar`;
        avatar.innerHTML = sender === "bot" ? "🤖" : "👤";

        const bubble = document.createElement("div");
        bubble.className = `message-bubble ${sender}-bubble`;
        bubble.innerHTML = this.formatMarkdown(text);

        row.appendChild(avatar);
        row.appendChild(bubble);
        this.messagesContainer.appendChild(row);
        this.scrollToBottom();
    },

    renderCard(card) {
        const cardEl = document.createElement("div");
        cardEl.className = "chat-embedded-card";

        let detailsHtml = "";
        if (card.details) {
            detailsHtml = "<div class='card-details-list'>";
            for (const [key, val] of Object.entries(card.details)) {
                detailsHtml += `<div><span>${key}:</span> <strong>${val}</strong></div>`;
            }
            detailsHtml += "</div>";
        }

        let actionsHtml = "";
        if (card.actions) {
            actionsHtml = "<div class='chat-card-actions'>";
            card.actions.forEach(act => {
                if (act.action.startsWith("download_memo:")) {
                    const id = act.action.split(":")[1];
                    actionsHtml += `<a href="/api/memo/${id}?format=download" class="btn btn-success btn-sm" download>📥 Download Memo</a>`;
                } else if (act.action.startsWith("print_memo:")) {
                    const id = act.action.split(":")[1];
                    actionsHtml += `<button class="btn btn-outline btn-sm" onclick="AppointmentsManager.viewHtmlMemo('${id}')">🖨️ View / Print</button>`;
                }
            });
            actionsHtml += "</div>";
        }

        cardEl.innerHTML = `
            <h5>${card.title}</h5>
            <p>${card.subtitle}</p>
            ${detailsHtml}
            ${actionsHtml}
        `;

        this.messagesContainer.appendChild(cardEl);
        this.scrollToBottom();
    },

    renderDownloadMemoBox(memoId) {
        const box = document.createElement("div");
        box.className = "memo-download-box";
        box.innerHTML = `
            <span>📄 Official Booking Confirmation Memo Ready</span>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
                <a href="/api/memo/${memoId}?format=download" class="btn btn-success btn-sm" download>
                    📥 Download Memo (.TXT)
                </a>
                <button class="btn btn-outline btn-sm" onclick="AppointmentsManager.viewHtmlMemo('${memoId}')">
                    🖨️ View & Print Memo Slip
                </button>
            </div>
        `;
        this.messagesContainer.appendChild(box);
    },

    renderQuickReplies(replies) {
        this.quickRepliesContainer.innerHTML = "";
        replies.forEach(replyText => {
            const pill = document.createElement("button");
            pill.className = "quick-reply-pill";
            pill.textContent = replyText;
            pill.addEventListener("click", () => {
                this.sendUserMessage(replyText);
            });
            this.quickRepliesContainer.appendChild(pill);
        });
    },

    showTypingIndicator() {
        const row = document.createElement("div");
        row.className = "message-row bot-row";
        row.innerHTML = `
            <div class="msg-avatar bot-avatar">🤖</div>
            <div class="message-bubble bot-bubble" style="color: #64748b; font-style: italic;">
                HealthBot is typing...
            </div>
        `;
        this.messagesContainer.appendChild(row);
        this.scrollToBottom();
        return row;
    },

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    },

    formatMarkdown(text) {
        if (!text) return "";
        let formatted = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Bold **text**
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        // Italic *text*
        formatted = formatted.replace(/\*(.*?)\*/g, "<em>$1</em>");
        // Inline code `code`
        formatted = formatted.replace(/`(.*?)`/g, "<code>$1</code>");
        // Bullet points
        formatted = formatted.replace(/• (.*?)(\n|$)/g, "<li style='margin-left: 16px;'>$1</li>");
        // Linebreaks
        formatted = formatted.replace(/\n/g, "<br>");

        return formatted;
    }
};

// ============================================================================
// Doctors Catalog Module
// ============================================================================
const DoctorsCatalog = {
    async init() {
        this.grid = document.getElementById("doctorsGrid");
        this.filterButtons = document.querySelectorAll(".filter-btn");

        this.bindEvents();
        await this.loadDoctors();
    },

    bindEvents() {
        this.filterButtons.forEach(btn => {
            btn.addEventListener("click", (e) => {
                this.filterButtons.forEach(b => b.classList.remove("active"));
                e.target.classList.add("active");
                const specialty = e.target.dataset.specialty || "";
                this.loadDoctors(specialty);
            });
        });
    },

    async loadDoctors(specialty = "") {
        try {
            const data = await ApiService.getDoctors(specialty);
            AppState.doctors = data.doctors;
            this.renderDoctors(data.doctors);
        } catch (err) {
            this.grid.innerHTML = `<p style="color:var(--danger)">Failed to load doctors catalog: ${err.message}</p>`;
        }
    },

    renderDoctors(doctors) {
        if (!doctors || doctors.length === 0) {
            this.grid.innerHTML = "<p style='color:var(--text-muted); grid-column: 1/-1; text-align: center;'>No doctors found matching this specialty.</p>";
            return;
        }

        this.grid.innerHTML = doctors.map(doc => {
            const initials = doc.name.replace("Dr. ", "").split(" ").map(n => n[0]).join("");
            return `
                <article class="doctor-card">
                    <div>
                        <div class="doc-header">
                            <div class="doc-avatar">${initials}</div>
                            <div class="doc-meta">
                                <h3>${doc.name}</h3>
                                <span class="doc-specialty-badge">${doc.specialty}</span>
                                <div class="doc-qual">${doc.qualification}</div>
                            </div>
                        </div>
                        <div class="doc-body">
                            <p class="doc-bio">${doc.bio}</p>
                            <div class="doc-stats-row">
                                <div class="doc-stat">Experience: <strong>${doc.experience_years} yrs</strong></div>
                                <div class="doc-stat">Rating: <strong>⭐ ${doc.rating}</strong></div>
                            </div>
                        </div>
                    </div>
                    <div class="doc-footer">
                        <div class="fee-display">Fee: <strong>$${doc.fee}</strong></div>
                        <div style="display:flex; gap:8px;">
                            <button class="btn btn-primary btn-sm" onclick="DoctorsCatalog.bookWithDoctor(${doc.id}, '${doc.name}', '${doc.specialty}')">
                                📅 Book Slot
                            </button>
                        </div>
                    </div>
                </article>
            `;
        }).join("");
    },

    bookWithDoctor(docId, docName, specialty) {
        if (AppState.role === "guest") {
            AuthManager.openLoginModal("patient");
            Toast.show("Please log in as Patient to book an appointment with " + docName, "warning");
            return;
        }

        // Open chatbot directly configured for booking this doctor
        ChatBot.openWindow();
        ChatBot.sendUserMessage(`I want to book an appointment with ${docName} for ${specialty}`);
    }
};

// ============================================================================
// Appointments Manager (Patient Portal & Cancellation)
// ============================================================================
const AppointmentsManager = {
    init() {
        this.tableBody = document.getElementById("patientAppointmentsBody");
        this.memoModal = document.getElementById("memoModal");
        this.memoFrame = document.getElementById("memoFrame");
        this.closeMemoBtn = document.getElementById("closeMemoModal");

        this.closeMemoBtn?.addEventListener("click", () => this.memoModal.close());
    },

    async loadPatientAppointments() {
        if (AppState.role !== "patient") return;

        try {
            const data = await ApiService.getAppointments();
            AppState.appointments = data.appointments;
            this.renderAppointments(data.appointments);
        } catch (err) {
            console.error("Failed to load patient appointments:", err);
        }
    },

    renderAppointments(appointments) {
        const tbody = document.getElementById("patientAppointmentsBody");
        if (!tbody) return;

        if (!appointments || appointments.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted); padding:24px;">No appointments found. Use HealthBot to schedule a consultation.</td></tr>`;
            return;
        }

        tbody.innerHTML = appointments.map(a => {
            const statusClass = a.status === "CONFIRMED" ? "status-confirmed" : (a.status === "CANCELLED" ? "status-cancelled" : "status-completed");
            const canCancel = a.status === "CONFIRMED";

            return `
                <tr>
                    <td><strong>${a.id}</strong></td>
                    <td>${a.doctor_name}</td>
                    <td><span class="doc-specialty-badge">${a.specialty}</span></td>
                    <td>${a.date}</td>
                    <td>${a.time_slot}</td>
                    <td><span class="status-badge ${statusClass}">${a.status}</span></td>
                    <td>
                        <div style="display:flex; gap:6px; flex-wrap:wrap;">
                            <a href="/api/memo/${a.id}?format=download" class="btn btn-outline btn-sm" download title="Download Memo">
                                📥 Memo
                            </a>
                            <button class="btn btn-outline btn-sm" onclick="AppointmentsManager.viewHtmlMemo('${a.id}')" title="Print Slip">
                                🖨️ Print
                            </button>
                            ${canCancel ? `
                                <button class="btn btn-danger btn-sm" onclick="AppointmentsManager.confirmCancel('${a.id}')" title="Cancel Appointment">
                                    ❌ Cancel
                                </button>
                            ` : `<span style="font-size:0.75rem; color:var(--text-muted); align-self:center;">—</span>`}
                        </div>
                    </td>
                </tr>
            `;
        }).join("");
    },

    async confirmCancel(appointmentId) {
        // Trigger conversational cancellation in HealthBot or prompt confirmation
        const confirmed = confirm(`Are you sure you want to cancel appointment ${appointmentId}?`);
        if (!confirmed) return;

        try {
            const res = await ApiService.cancelAppointment(appointmentId);
            Toast.show(res.message, "success");
            this.loadPatientAppointments();
            // Also inform chat if open
            ChatBot.sendBotMessage(`ℹ️ Appointment **${appointmentId}** has been cancelled.`);
        } catch (err) {
            Toast.show(err.message || "Failed to cancel appointment", "danger");
        }
    },

    viewHtmlMemo(appointmentId) {
        if (!this.memoModal || !this.memoFrame) return;
        const memoBase = (window.location.protocol.startsWith("http") && window.location.port && window.location.port !== "8000")
            ? `http://${window.location.hostname}:8000`
            : "";
        this.memoFrame.src = `${memoBase}/api/memo/${appointmentId}?format=html`;
        this.memoModal.showModal();
    }
};

// ============================================================================
// Admin Dashboard Module
// ============================================================================
const AdminDashboard = {
    init() {
        this.tableBody = document.getElementById("adminAppointmentsBody");
        this.searchInput = document.getElementById("adminSearchInput");
        this.statusFilter = document.getElementById("adminStatusFilter");
        this.refreshBtn = document.getElementById("adminRefreshBtn");

        this.bindEvents();
    },

    bindEvents() {
        this.searchInput?.addEventListener("input", () => this.filterAdminTable());
        this.statusFilter?.addEventListener("change", () => this.filterAdminTable());
        this.refreshBtn?.addEventListener("click", () => this.loadDashboard());
    },

    async loadDashboard() {
        if (AppState.role !== "admin") return;

        try {
            // Load stats and all appointments
            const [stats, apptsData] = await Promise.all([
                ApiService.getStats(),
                ApiService.getAppointments()
            ]);

            AppState.stats = stats;
            AppState.appointments = apptsData.appointments;

            this.renderMetrics(stats);
            this.renderCharts(stats);
            this.renderAdminTable(apptsData.appointments);
        } catch (err) {
            console.error("Failed to load admin dashboard:", err);
            Toast.show("Admin dashboard error: " + err.message, "danger");
        }
    },

    renderMetrics(stats) {
        document.getElementById("statTotalAppts").textContent = stats.total_appointments;
        document.getElementById("statConfirmedAppts").textContent = stats.confirmed_appointments;
        document.getElementById("statCancelledAppts").textContent = stats.cancelled_appointments;
        document.getElementById("statTodayAppts").textContent = stats.today_appointments;
        document.getElementById("statUniquePatients").textContent = stats.unique_patients;
        document.getElementById("statTotalDoctors").textContent = stats.total_doctors;
    },

    renderCharts(stats) {
        const specialtyContainer = document.getElementById("chartSpecialtyBars");
        const workloadContainer = document.getElementById("chartWorkloadBars");

        // Specialty bar chart
        if (specialtyContainer && stats.by_specialty) {
            const maxSpec = Math.max(...stats.by_specialty.map(s => s.count), 1);
            specialtyContainer.innerHTML = stats.by_specialty.map(item => {
                const pct = Math.round((item.count / maxSpec) * 100);
                return `
                    <div class="bar-row">
                        <span class="bar-label" title="${item.specialty}">${item.specialty}</span>
                        <div class="bar-track">
                            <div class="bar-fill" style="width: ${pct}%"></div>
                        </div>
                        <span class="bar-value">${item.count}</span>
                    </div>
                `;
            }).join("");
        }

        // Doctor workload bar chart
        if (workloadContainer && stats.doctor_workload) {
            const maxWork = Math.max(...stats.doctor_workload.map(w => w.bookings), 1);
            workloadContainer.innerHTML = stats.doctor_workload.map(item => {
                const pct = Math.round((item.bookings / maxWork) * 100);
                return `
                    <div class="bar-row">
                        <span class="bar-label" title="${item.doctor_name}">${item.doctor_name}</span>
                        <div class="bar-track">
                            <div class="bar-fill" style="width: ${pct}%"></div>
                        </div>
                        <span class="bar-value">${item.bookings}</span>
                    </div>
                `;
            }).join("");
        }
    },

    renderAdminTable(appointments) {
        const tbody = document.getElementById("adminAppointmentsBody");
        if (!tbody) return;

        if (!appointments || appointments.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding:24px;">No appointments records found.</td></tr>`;
            return;
        }

        tbody.innerHTML = appointments.map(a => {
            const statusClass = a.status === "CONFIRMED" ? "status-confirmed" : (a.status === "CANCELLED" ? "status-cancelled" : "status-completed");
            const canCancel = a.status === "CONFIRMED";

            return `
                <tr>
                    <td><strong>${a.id}</strong></td>
                    <td>${a.patient_name} <br><small style="color:var(--text-muted)">@${a.patient_username}</small></td>
                    <td>${a.doctor_name}</td>
                    <td><span class="doc-specialty-badge">${a.specialty}</span></td>
                    <td>${a.date}</td>
                    <td>${a.time_slot}</td>
                    <td><span class="status-badge ${statusClass}">${a.status}</span></td>
                    <td>
                        <div style="display:flex; gap:6px;">
                            <a href="/api/memo/${a.id}?format=download" class="btn btn-outline btn-sm" download title="Download Memo">
                                📥
                            </a>
                            <button class="btn btn-outline btn-sm" onclick="AppointmentsManager.viewHtmlMemo('${a.id}')" title="Print Slip">
                                🖨️
                            </button>
                            ${canCancel ? `
                                <button class="btn btn-danger btn-sm" onclick="AdminDashboard.adminCancel('${a.id}')" title="Admin Cancel">
                                    ❌
                                </button>
                            ` : ""}
                        </div>
                    </td>
                </tr>
            `;
        }).join("");
    },

    filterAdminTable() {
        const search = (this.searchInput?.value || "").toLowerCase();
        const status = (this.statusFilter?.value || "");

        const filtered = AppState.appointments.filter(a => {
            const matchSearch = a.id.toLowerCase().includes(search) ||
                                a.patient_name.toLowerCase().includes(search) ||
                                a.doctor_name.toLowerCase().includes(search) ||
                                a.specialty.toLowerCase().includes(search);
            const matchStatus = !status || a.status === status;
            return matchSearch && matchStatus;
        });

        this.renderAdminTable(filtered);
    },

    async adminCancel(appointmentId) {
        const confirmed = confirm(`[ADMIN ACTION] Are you sure you want to cancel appointment ${appointmentId}?`);
        if (!confirmed) return;

        try {
            const res = await ApiService.cancelAppointment(appointmentId, "Admin override cancellation");
            Toast.show(res.message, "success");
            this.loadDashboard();
        } catch (err) {
            Toast.show(err.message || "Failed to cancel appointment", "danger");
        }
    }
};

// ============================================================================
// Application Startup Initialization
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
    AuthManager.init();
    ChatBot.init();
    DoctorsCatalog.init();
    AppointmentsManager.init();
    AdminDashboard.init();
});
