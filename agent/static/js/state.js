/**
 * Global State Management
 * Student Opportunity Intelligence Platform
 */

const State = {
    // Current active role: 'admin' or 'student'
    role: localStorage.getItem("soi_role") || "admin",
    
    // Theme: 'light' (default) or 'dark'
    theme: localStorage.getItem("soi_theme") || "light",
    
    // Active Navigation Route / View ID
    activeView: "admin-dashboard",
    
    // Active Student Profile (for Student Portal)
    currentStudent: null,
    
    // Cached collections
    studentsList: [],
    savedOpportunityIds: new Set(),
    notifications: [],
    unreadNotificationsCount: 0,
    
    // System Settings cache
    settings: {},

    init() {
        this.applyTheme(this.theme);
    },

    setRole(newRole) {
        this.role = newRole;
        localStorage.setItem("soi_role", newRole);
        document.body.setAttribute("data-role", newRole);
        
        // Update role badge in UI
        const badge = document.getElementById("current-role-badge");
        if (badge) {
            badge.textContent = newRole === "admin" ? "Admin Control Center" : "Student Portal";
        }
        
        // Update nav visibility
        document.querySelectorAll(".nav-group-admin").forEach(el => {
            el.style.display = newRole === "admin" ? "block" : "none";
        });
        document.querySelectorAll(".nav-group-student").forEach(el => {
            el.style.display = newRole === "student" ? "block" : "none";
        });
    },

    setTheme(newTheme) {
        this.theme = newTheme;
        localStorage.setItem("soi_theme", newTheme);
        this.applyTheme(newTheme);
    },

    applyTheme(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        const btn = document.getElementById("theme-toggle-btn");
        if (btn) {
            btn.innerHTML = theme === "dark" 
                ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`
                : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
            btn.setAttribute("title", `Switch to ${theme === "dark" ? "Light" : "Dark"} Mode`);
        }
    },

    toggleTheme() {
        const next = this.theme === "dark" ? "light" : "dark";
        this.setTheme(next);
    },

    toggleRole() {
        const next = this.role === "admin" ? "student" : "admin";
        this.setRole(next);
        const defaultView = next === "admin" ? "admin-dashboard" : "student-dashboard";
        window.location.hash = `#${defaultView}`;
    },

    async refreshNotifications() {
        try {
            const sid = this.currentStudent ? this.currentStudent.id : null;
            const res = await API.getNotifications(sid);
            this.notifications = res.notifications || [];
            this.unreadNotificationsCount = this.notifications.filter(n => !n.read_at).length;
            
            const badge = document.getElementById("topbar-notification-badge");
            if (badge) {
                if (this.unreadNotificationsCount > 0) {
                    badge.textContent = this.unreadNotificationsCount;
                    badge.style.display = "block";
                } else {
                    badge.style.display = "none";
                }
            }
        } catch (e) {
            console.error("Failed to load notifications:", e);
        }
    },

    async refreshSavedOpportunities() {
        if (!this.currentStudent) return;
        try {
            const res = await API.getSavedOpportunities(this.currentStudent.id);
            const savedList = res.saved || [];
            this.savedOpportunityIds = new Set(savedList.map(o => o.id));
        } catch (e) {
            console.error("Failed to load saved opportunities:", e);
        }
    }
};

window.State = State;
