/**
 * API Client for Student Opportunity Intelligence Platform
 * Handles authentication, typed requests, error interception, and file downloads.
 */

const API = {
    async request(endpoint, options = {}) {
        const config = {
            headers: {
                "Content-Type": "application/json",
                ...options.headers
            },
            ...options
        };

        if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
            config.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(endpoint, config);
            if (!response.ok) {
                let errDetail = "Request failed";
                try {
                    const errJson = await response.json();
                    errDetail = errJson.detail || errJson.message || response.statusText;
                } catch (e) {
                    errDetail = await response.text();
                }
                throw new Error(errDetail || `HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    },

    // 1. Health & Admin Telemetry
    async getHealth() {
        return this.request("/api/health");
    },

    async getAdminMetrics() {
        return this.request("/api/admin/metrics");
    },

    async getOrchestratorStatus() {
        return this.request("/api/orchestrator/status");
    },

    async triggerOrchestrator(generateReports = false) {
        return this.request(`/api/orchestrator/run?generate_reports=${generateReports}`, { method: "POST" });
    },

    // 2. Opportunities Management
    async getOpportunities(params = {}) {
        const query = new URLSearchParams();
        for (const [k, v] of Object.entries(params)) {
            if (v !== undefined && v !== null && v !== "" && v !== "all") {
                query.append(k, v);
            }
        }
        return this.request(`/api/opportunities?${query.toString()}`);
    },

    async getOpportunity(id) {
        return this.request(`/api/opportunities/${id}`);
    },

    async updateOpportunity(id, data) {
        return this.request(`/api/opportunities/${id}`, {
            method: "PUT",
            body: data
        });
    },

    // 3. Verification & Quality Control
    async getVerificationQueue(limit = 50) {
        return this.request(`/api/admin/verification-queue?limit=${limit}`);
    },

    async reviewVerification(oppId, decision, reason = "") {
        return this.request(`/api/admin/verification-queue/${oppId}/review`, {
            method: "POST",
            body: { decision, reason }
        });
    },

    // 4. AI Agents Management
    async getAgents() {
        return this.request("/api/admin/agents");
    },

    async runAgent(agentId) {
        return this.request(`/api/admin/agents/${agentId}/run`, { method: "POST" });
    },

    // 5. Sources Registry
    async getSources() {
        return this.request("/api/admin/sources");
    },

    async saveSource(sourceData) {
        return this.request("/api/admin/sources", {
            method: "POST",
            body: sourceData
        });
    },

    async testSource(url) {
        return this.request("/api/admin/sources/test", {
            method: "POST",
            body: { url }
        });
    },

    // 6. 20-Report Center
    async getReports() {
        return this.request("/api/reports");
    },

    async generateReport(reportNumber, formats = ["pdf", "xlsx", "csv", "html"]) {
        return this.request("/api/reports/generate", {
            method: "POST",
            body: { report_number: String(reportNumber).padStart(2, "0"), formats }
        });
    },

    async getReportHistory(limit = 50) {
        return this.request(`/api/reports/history?limit=${limit}`);
    },

    // 7. Schedules & Automation
    async getSchedules() {
        return this.request("/api/admin/schedules");
    },

    async triggerSchedule(scheduleId) {
        return this.request(`/api/admin/schedules/${scheduleId}/trigger`, { method: "POST" });
    },

    // 8. Students & Matching
    async getStudents() {
        return this.request("/api/students");
    },

    async getStudent(id) {
        return this.request(`/api/students/${id}`);
    },

    async saveStudent(profileData) {
        return this.request("/api/students", {
            method: "POST",
            body: profileData
        });
    },

    async getMatches(studentId, topN = 20) {
        return this.request(`/api/matches/${studentId}?top_n=${topN}`);
    },

    async getSavedOpportunities(studentId) {
        return this.request(`/api/students/${studentId}/saved`);
    },

    async toggleSavedOpportunity(studentId, opportunityId) {
        return this.request(`/api/students/${studentId}/saved`, {
            method: "POST",
            body: { student_id: studentId, opportunity_id: opportunityId }
        });
    },

    // 9. Kanban Application Tracker
    async getApplications(studentId) {
        return this.request(`/api/applications/${studentId}`);
    },

    async createApplication(studentId, opportunityId, status = "interested", notes = "") {
        return this.request("/api/applications", {
            method: "POST",
            body: { student_id: studentId, opportunity_id: opportunityId, status, notes }
        });
    },

    async updateApplicationStatus(applicationId, studentId, newStatus, notes = "") {
        return this.request("/api/applications/status", {
            method: "POST",
            body: { application_id: applicationId, student_id: studentId, new_status: newStatus, notes }
        });
    },

    async addApplicationTask(applicationId, studentId, taskTitle) {
        return this.request("/api/applications/task", {
            method: "POST",
            body: { application_id: applicationId, student_id: studentId, task_title: taskTitle }
        });
    },

    async toggleApplicationTask(applicationId, studentId, taskId) {
        return this.request(`/api/applications/task/toggle?application_id=${applicationId}&student_id=${studentId}&task_id=${taskId}`, {
            method: "POST"
        });
    },

    async getPrepPacket(studentId, opportunityId) {
        return this.request(`/api/prep-packet?student_id=${studentId}&opportunity_id=${opportunityId}`, {
            method: "POST"
        });
    },

    // 10. Notifications
    async getNotifications(studentId = null) {
        const query = studentId ? `?student_id=${studentId}` : "";
        return this.request(`/api/notifications${query}`);
    },

    async markNotificationRead(id) {
        return this.request(`/api/notifications/${id}/read`, { method: "POST" });
    },

    async markAllNotificationsRead(studentId = null) {
        return this.request("/api/notifications/mark-all-read", {
            method: "POST",
            body: { student_id: studentId }
        });
    },

    // 11. System Settings & Audit Logs
    async getSettings() {
        return this.request("/api/admin/settings");
    },

    async saveSettings(settingsData) {
        return this.request("/api/admin/settings", {
            method: "POST",
            body: settingsData
        });
    },

    async getAuditLogs(limit = 100) {
        return this.request(`/api/admin/audit-logs?limit=${limit}`);
    },

    // 12. Global Search
    async search(query) {
        return this.request(`/api/search?q=${encodeURIComponent(query)}`);
    }
};

window.API = API;
