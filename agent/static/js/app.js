/**
 * Main Application Controller & Router
 * Student Opportunity Intelligence Platform
 */

// Global Router
function showView(viewId) {
    if (!viewId) viewId = State.role === "admin" ? "admin-dashboard" : "student-dashboard";

    // Update active state in state store
    State.activeView = viewId;
    window.location.hash = `#${viewId}`;

    // Hide all view panels
    document.querySelectorAll(".view-panel").forEach(p => p.classList.remove("active"));

    // Deactivate all sidebar nav links
    document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));

    // Activate current panel
    const target = document.getElementById(`view-${viewId}`);
    if (target) {
        target.classList.add("active");
    }

    // Activate corresponding nav link
    const activeLink = document.querySelector(`.nav-link[data-view="${viewId}"]`);
    if (activeLink) {
        activeLink.classList.add("active");
    }

    // Close mobile drawer if open
    closeMobileSidebar();

    // Call view renderer
    switch (viewId) {
        case "admin-dashboard":
            ViewsAdmin.renderDashboard();
            break;
        case "admin-agents":
            ViewsAdmin.renderAgents();
            break;
        case "admin-workflows":
            ViewsAdmin.renderWorkflows();
            break;
        case "admin-opportunities":
            ViewsAdmin.renderOpportunities();
            break;
        case "admin-verification":
            ViewsAdmin.renderVerificationQueue();
            break;
        case "admin-sources":
            ViewsAdmin.renderSources();
            break;
        case "admin-reports":
            ViewsAdmin.renderReports();
            break;
        case "admin-schedules":
            ViewsAdmin.renderSchedules();
            break;
        case "admin-students":
            ViewsAdmin.renderStudents();
            break;
        case "admin-settings":
            ViewsAdmin.renderSettings();
            break;
        case "admin-health":
            ViewsAdmin.renderHealthAndAudit();
            break;
        case "student-dashboard":
            ViewsStudent.renderDashboard();
            break;
        case "student-opportunities":
            ViewsStudent.renderOpportunities();
            break;
        case "student-recommendations":
            ViewsStudent.renderRecommendations();
            break;
        case "student-saved":
            ViewsStudent.renderSaved();
            break;
        case "student-applications":
            ViewsStudent.renderApplications();
            break;
        case "student-profile":
            ViewsStudent.renderProfile();
            break;
        case "notifications":
            ViewsStudent.renderNotifications();
            break;
    }
}

// Mobile sidebar controls
function toggleMobileSidebar() {
    const sidebar = document.getElementById("main-sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    if (sidebar) sidebar.classList.toggle("mobile-open");
    if (overlay) overlay.classList.toggle("active");
}

function closeMobileSidebar() {
    const sidebar = document.getElementById("main-sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    if (sidebar) sidebar.classList.remove("mobile-open");
    if (overlay) overlay.classList.remove("active");
}

// Global Search
let searchDebounceTimeout = null;
function handleGlobalSearch(query) {
    clearTimeout(searchDebounceTimeout);
    const dropdown = document.getElementById("search-results-dropdown");
    if (!dropdown) return;

    if (!query || query.trim().length < 2) {
        dropdown.classList.remove("active");
        dropdown.innerHTML = "";
        return;
    }

    searchDebounceTimeout = setTimeout(async () => {
        try {
            const res = await API.search(query.trim());
            const opps = res.opportunities || [];
            const sources = res.sources || [];
            const students = res.students || [];

            if (opps.length === 0 && sources.length === 0 && students.length === 0) {
                dropdown.innerHTML = `<div style="padding: 1rem; text-align: center; color: var(--text-muted); font-size: 0.82rem;">No matching entities found.</div>`;
                dropdown.classList.add("active");
                return;
            }

            let html = "";
            if (opps.length > 0) {
                html += `<div class="search-group-header">Opportunities (${opps.length})</div>`;
                opps.slice(0, 5).forEach(o => {
                    html += `
                        <div class="search-result-item" onclick="openOpportunityDetail('${o.id}')">
                            <span class="search-result-title">${o.name}</span>
                            <span class="search-result-meta">${o.sponsor} • ${o.category || 'Opportunity'}</span>
                        </div>
                    `;
                });
            }

            if (sources.length > 0) {
                html += `<div class="search-group-header">Sources & Portals (${sources.length})</div>`;
                sources.forEach(s => {
                    html += `
                        <div class="search-result-item" onclick="showView('admin-sources')">
                            <span class="search-result-title">${s.name}</span>
                            <span class="search-result-meta">${s.url}</span>
                        </div>
                    `;
                });
            }

            if (students.length > 0) {
                html += `<div class="search-group-header">Students (${students.length})</div>`;
                students.forEach(st => {
                    html += `
                        <div class="search-result-item" onclick="switchToStudentView('${st.id}')">
                            <span class="search-result-title">${st.full_name}</span>
                            <span class="search-result-meta">${st.university} • ${st.discipline}</span>
                        </div>
                    `;
                });
            }

            dropdown.innerHTML = html;
            dropdown.classList.add("active");
        } catch (e) {
            console.error("Search error:", e);
        }
    }, 250);
}

// Opportunity Details Modal / Drawer
async function openOpportunityDetail(oppId) {
    try {
        const opp = await API.getOpportunity(oppId);
        if (!opp) return;

        const body = `
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                <div>
                    <h3 style="font-size: 1.2rem; font-weight: 700; color: var(--text-primary);">${opp.name}</h3>
                    <div style="font-size: 0.85rem; color: var(--text-muted);">${opp.sponsor} • ID: <code>${opp.id}</code></div>
                </div>

                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    ${UI.renderStatusBadge(opp.status, opp.days_left)}
                    ${UI.renderVerificationBadge(opp.verification_badge, opp.source_trust_tier)}
                    ${UI.renderSectorBadge(opp.university_types)}
                    ${UI.renderPriorityBadges(opp)}
                </div>

                <div class="card" style="margin-bottom: 0;">
                    <div class="card-header"><h4 class="card-title">Criteria & Requirements</h4></div>
                    <div class="card-body" style="font-size: 0.85rem; display: flex; flex-direction: column; gap: 6px;">
                        <div>Eligible Semesters: <strong>${opp.eligible_semesters ? JSON.stringify(opp.eligible_semesters) : '1-8'}</strong></div>
                        <div>Degree Levels: <strong>${opp.degree_levels || 'Undergraduate'}</strong></div>
                        <div>Fields / Disciplines: <strong>${opp.fields_of_study || 'All fields'}</strong></div>
                        <div>Merit / CGPA Requirement: <strong>${opp.min_gpa_or_marks || opp.merit_criteria || 'not stated'}</strong></div>
                        <div>Financial Need Criteria: <strong>${opp.need_criteria || 'not stated'}</strong></div>
                        <div>Domicile: <strong>${opp.domicile_requirements || 'KP / Pakistan'}</strong></div>
                    </div>
                </div>

                <div class="card" style="margin-bottom: 0;">
                    <div class="card-header"><h4 class="card-title">Funding & Benefits</h4></div>
                    <div class="card-body" style="font-size: 0.85rem;">
                        <p>${opp.benefits && opp.benefits !== 'not stated' ? opp.benefits : 'Detailed funding package not stated in announcement.'}</p>
                        ${opp.award_amount && opp.award_amount !== 'not stated' ? `<div style="margin-top: 0.5rem;"><strong>Award Amount:</strong> ${opp.award_amount}</div>` : ""}
                    </div>
                </div>

                <div class="card" style="margin-bottom: 0;">
                    <div class="card-header"><h4 class="card-title">Official Evidence & Provenance</h4></div>
                    <div class="card-body" style="font-size: 0.82rem;">
                        <blockquote style="border-left: 3px solid var(--primary); padding-left: 0.75rem; color: var(--text-secondary); font-style: italic; margin-bottom: 0.75rem;">
                            "${opp.evidence_quote || 'No verbatim excerpt recorded.'}"
                        </blockquote>
                        <div>Official Portal: <a href="${opp.apply_url}" target="_blank" rel="noopener noreferrer" style="color: var(--primary);">${opp.apply_url}</a></div>
                        <div>Source Announcement: <a href="${opp.source_url}" target="_blank" rel="noopener noreferrer" style="color: var(--primary);">${opp.source_url}</a></div>
                    </div>
                </div>
            </div>
        `;

        const footer = `
            <button class="btn btn-outline" onclick="UI.closeDrawer()">Close</button>
            ${opp.apply_url && opp.apply_url !== 'not stated' ? `<a href="${opp.apply_url}" target="_blank" rel="noopener noreferrer" class="btn btn-primary">Apply on Official Portal &rarr;</a>` : ""}
        `;

        UI.openDrawer("Opportunity Details", body, footer);
    } catch (e) {
        UI.showToast(`Error opening opportunity: ${e.message}`, "error");
    }
}

// Trigger Full Pipeline
async function triggerFullPipeline() {
    UI.showToast("Triggering full Master Orchestrator multi-agent cycle...", "info");
    try {
        const res = await API.triggerOrchestrator(true);
        UI.showToast(`Orchestrator executed successfully: ${res.status || 'SUCCESS'}`, "success");
        if (State.activeView === "admin-dashboard") ViewsAdmin.renderDashboard();
    } catch (e) {
        UI.showToast(`Workflow execution error: ${e.message}`, "error");
    }
}

// Trigger Deadline Scan
async function triggerDeadlineScan() {
    UI.showToast("Scanning closing deadlines across all opportunities...", "info");
    try {
        const res = await API.runAgent("deadline_monitor");
        UI.showToast("Deadlines scanned and notifications dispatched idempotently.", "success");
        await State.refreshNotifications();
    } catch (e) {
        UI.showToast(`Scan failed: ${e.message}`, "error");
    }
}

// Report Generation Prompt Modal
function generateReportPrompt(reportNum) {
    const num = String(reportNum).padStart(2, "0");
    const body = `
        <div style="font-size: 0.85rem; line-height: 1.5;">
            <p>Generate publication-grade report <strong>#${num}</strong> from the verified database.</p>
            <div style="margin-top: 1rem;">
                <label style="font-weight: 700; margin-bottom: 0.5rem; display: block;">Select Output Formats:</label>
                <div style="display: flex; gap: 1rem;">
                    <label><input type="checkbox" id="gen-fmt-pdf" checked> PDF (Vector Canvas)</label>
                    <label><input type="checkbox" id="gen-fmt-xlsx" checked> Excel (XLSX)</label>
                    <label><input type="checkbox" id="gen-fmt-csv" checked> CSV (UTF-8-SIG)</label>
                    <label><input type="checkbox" id="gen-fmt-html" checked> HTML</label>
                </div>
            </div>
        </div>
    `;
    const footer = `
        <button class="btn btn-outline" onclick="UI.closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="executeReportGeneration('${num}')">Generate Report</button>
    `;
    UI.showModal(`Generate Report ${num}`, body, footer);
}

async function executeReportGeneration(reportNum) {
    const formats = [];
    if (document.getElementById("gen-fmt-pdf")?.checked) formats.push("pdf");
    if (document.getElementById("gen-fmt-xlsx")?.checked) formats.push("xlsx");
    if (document.getElementById("gen-fmt-csv")?.checked) formats.push("csv");
    if (document.getElementById("gen-fmt-html")?.checked) formats.push("html");

    UI.closeModal();
    UI.showToast(`Compiling Report #${reportNum}...`, "info");

    try {
        const res = await API.generateReport(reportNum, formats);
        UI.showToast(`Report ${reportNum} compiled: ${res.record_count} records.`, "success");
        ViewsAdmin.renderReports();
    } catch (e) {
        UI.showToast(`Report generation failed: ${e.message}`, "error");
    }
}

async function generateAllReports() {
    UI.showToast("Initiating full compilation of all 20 standardized publication reports...", "info");
    try {
        for (let i = 1; i <= 20; i++) {
            const num = String(i).padStart(2, "0");
            await API.generateReport(num, ["pdf", "xlsx", "csv", "html"]);
        }
        UI.showToast("All 20 reports successfully compiled and archived in reports/", "success");
        ViewsAdmin.renderReports();
    } catch (e) {
        UI.showToast(`Batch report compilation error: ${e.message}`, "error");
    }
}

// Verification Queue Actions
async function reviewVerificationDecision(oppId, decision) {
    UI.showToast(`Submitting review decision [${decision.toUpperCase()}]...`, "info");
    try {
        await API.reviewVerification(oppId, decision);
        UI.showToast(`Opportunity #${oppId} updated: ${decision}`, "success");
        ViewsAdmin.renderVerificationQueue();
    } catch (e) {
        UI.showToast(`Review failed: ${e.message}`, "error");
    }
}

// Student Bookmark / Save
async function toggleSaveOpportunity(oppId) {
    if (!State.currentStudent) {
        UI.showToast("Please select or create a student profile first.", "warning");
        return;
    }
    try {
        const res = await API.toggleSavedOpportunity(State.currentStudent.id, oppId);
        if (res.is_saved) {
            State.savedOpportunityIds.add(oppId);
            UI.showToast("Opportunity bookmarked!", "success");
        } else {
            State.savedOpportunityIds.delete(oppId);
            UI.showToast("Bookmark removed.", "info");
        }
        
        // Re-render current view if needed
        if (State.activeView === "student-saved") {
            ViewsStudent.renderSaved();
        } else if (State.activeView === "student-opportunities") {
            const card = document.getElementById(`opp-card-${oppId}`);
            if (card) ViewsStudent.renderOpportunities();
        }
    } catch (e) {
        UI.showToast(`Failed to update bookmark: ${e.message}`, "error");
    }
}

// Student Kanban Tracker
async function trackOpportunity(oppId) {
    if (!State.currentStudent) {
        UI.showToast("Please select a student profile.", "warning");
        return;
    }
    try {
        await API.createApplication(State.currentStudent.id, oppId, "interested");
        UI.showToast("Added to your Applications Kanban Board!", "success");
        if (State.activeView === "student-applications") {
            ViewsStudent.renderApplications();
        }
    } catch (e) {
        UI.showToast(`Error tracking opportunity: ${e.message}`, "error");
    }
}

async function moveApplicationStatus(appId, newStatus) {
    if (!State.currentStudent) return;
    try {
        await API.updateApplicationStatus(appId, State.currentStudent.id, newStatus);
        UI.showToast(`Moved to ${newStatus.replace('_', ' ')}`, "success");
        ViewsStudent.renderApplications();
    } catch (e) {
        UI.showToast(`Move failed: ${e.message}`, "error");
    }
}

function openPrepWorkspace(oppId) {
    ViewsStudent.renderPrepWorkspace(oppId);
}

// Switch to student view for a specific student
async function switchToStudentView(studentId) {
    try {
        const student = await API.getStudent(studentId);
        if (student) {
            State.currentStudent = student;
            State.setRole("student");
            showView("student-dashboard");
            UI.showToast(`Viewing as ${student.full_name}`, "info");
        }
    } catch (e) {
        UI.showToast(`Failed to switch student: ${e.message}`, "error");
    }
}

// Save Student Profile
async function saveStudentProfileForm() {
    const profile = {
        id: State.currentStudent ? State.currentStudent.id : undefined,
        full_name: document.getElementById("prof-name")?.value || "Student",
        email: document.getElementById("prof-email")?.value || "student@example.com",
        university: document.getElementById("prof-uni")?.value || "University of Peshawar",
        university_type: document.getElementById("prof-sector")?.value || "public",
        degree_level: document.getElementById("prof-degree")?.value || "Undergraduate",
        discipline: document.getElementById("prof-discipline")?.value || "Computer Science",
        current_semester: parseInt(document.getElementById("prof-semester")?.value || "4"),
        cgpa: parseFloat(document.getElementById("prof-cgpa")?.value || "3.2"),
        domicile_district: document.getElementById("prof-district")?.value || "Charsadda",
        domicile_province: document.getElementById("prof-province")?.value || "Khyber Pakhtunkhwa"
    };

    UI.showToast("Saving student profile...", "info");
    try {
        const res = await API.saveStudent(profile);
        UI.showToast("Profile updated successfully!", "success");
        State.currentStudent = await API.getStudent(res.student_id);
        showView("student-recommendations");
    } catch (e) {
        UI.showToast(`Failed to save profile: ${e.message}`, "error");
    }
}

// Save Settings
async function savePlatformSettings() {
    const settings = {
        platform_name: document.getElementById("setting-platform-name")?.value,
        subtitle: document.getElementById("setting-subtitle")?.value,
        ai_model: document.getElementById("setting-ai-model")?.value,
        max_daily_budget_usd: parseFloat(document.getElementById("setting-budget")?.value || "5.0"),
        charsadda_priority_weight: parseFloat(document.getElementById("setting-charsadda-weight")?.value || "1.2"),
        owner_email: document.getElementById("setting-owner-email")?.value,
        resend_from_email: document.getElementById("setting-resend-sender")?.value,
        schedule_time: document.getElementById("setting-schedule-time")?.value
    };

    UI.showToast("Saving system configuration...", "info");
    try {
        await API.saveSettings(settings);
        UI.showToast("Platform settings saved and applied.", "success");
    } catch (e) {
        UI.showToast(`Error saving settings: ${e.message}`, "error");
    }
}

// Notification Actions
async function markNotificationSingleRead(id) {
    try {
        await API.markNotificationRead(id);
        await State.refreshNotifications();
        ViewsStudent.renderNotifications();
    } catch (e) {
        console.error(e);
    }
}

async function markAllNotificationsAsRead() {
    try {
        const sid = State.currentStudent ? State.currentStudent.id : null;
        await API.markAllNotificationsRead(sid);
        await State.refreshNotifications();
        ViewsStudent.renderNotifications();
        UI.showToast("All notifications marked as read.", "success");
    } catch (e) {
        console.error(e);
    }
}

// Filter triggers
function applyAdminOppFilters() {
    const filters = {
        search: document.getElementById("admin-opp-search")?.value,
        category: document.getElementById("admin-opp-category")?.value,
        university_type: document.getElementById("admin-opp-sector")?.value,
        semester: document.getElementById("admin-opp-semester")?.value,
        status: document.getElementById("admin-opp-status")?.value
    };
    ViewsAdmin.renderOpportunities(filters);
}

function resetAdminOppFilters() {
    ViewsAdmin.renderOpportunities({});
}

function applyStudentOppFilters() {
    const filters = {
        search: document.getElementById("student-opp-search")?.value,
        category: document.getElementById("student-opp-category")?.value,
        university_type: document.getElementById("student-opp-sector")?.value,
        semester: document.getElementById("student-opp-semester")?.value,
        status: document.getElementById("student-opp-status")?.value
    };
    ViewsStudent.renderOpportunities(filters);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        UI.showToast("Template copied to clipboard!", "success");
    });
}

// Add Source Modal
function openAddSourceModal() {
    const body = `
        <div style="display: flex; flex-direction: column; gap: 1rem;">
            <div class="form-group">
                <label class="form-label">Source Name</label>
                <input type="text" id="src-name" class="form-control" placeholder="e.g. UET Peshawar Financial Aid">
            </div>
            <div class="form-group">
                <label class="form-label">Portal URL</label>
                <input type="url" id="src-url" class="form-control" placeholder="https://uetpeshawar.edu.pk/scholarships">
            </div>
            <div class="form-group">
                <label class="form-label">Category</label>
                <select id="src-cat" class="form-select">
                    <option value="university">University Official Portal</option>
                    <option value="government">Government Education Portal</option>
                    <option value="foundation">Foundation / Trust</option>
                    <option value="international">International Body</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Trust Tier</label>
                <select id="src-tier" class="form-select">
                    <option value="1">Tier 1: Direct Official Domain (.gov.pk / .edu.pk)</option>
                    <option value="2">Tier 2: Official Secondary / Partner</option>
                    <option value="3">Tier 3: Unofficial Discovery Portal</option>
                </select>
            </div>
        </div>
    `;
    const footer = `
        <button class="btn btn-outline" onclick="UI.closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="saveNewSourceForm()">Add Source</button>
    `;
    UI.showModal("Register New Official Source", body, footer);
}

async function saveNewSourceForm() {
    const name = document.getElementById("src-name")?.value;
    const url = document.getElementById("src-url")?.value;
    const category = document.getElementById("src-cat")?.value;
    const tier = parseInt(document.getElementById("src-tier")?.value || "1");

    if (!url || !name) {
        UI.showToast("Please provide both name and URL.", "warning");
        return;
    }

    try {
        await API.saveSource({ name, url, category, tier });
        UI.closeModal();
        UI.showToast("New source registered successfully!", "success");
        ViewsAdmin.renderSources();
    } catch (e) {
        UI.showToast(`Failed to add source: ${e.message}`, "error");
    }
}

async function testSourceConnectivity(url) {
    UI.showToast(`Testing connectivity to ${url}...`, "info");
    try {
        const res = await API.testSource(url);
        UI.showToast(`Connection test: ${res.status === 200 ? 'SUCCESS (HTTP 200)' : 'HTTP ' + res.status}`, res.status === 200 ? "success" : "warning");
    } catch (e) {
        UI.showToast(`Connection failed: ${e.message}`, "error");
    }
}

// App Initialization
document.addEventListener("DOMContentLoaded", async () => {
    State.init();

    // Load registered students
    try {
        const res = await API.getStudents();
        State.studentsList = res.students || [];
        if (State.studentsList.length > 0) {
            State.currentStudent = State.studentsList[0];
            await State.refreshSavedOpportunities();
        }
        await State.refreshNotifications();
    } catch (e) {
        console.error("Initial load error:", e);
    }

    // Set initial role view
    State.setRole(State.role);

    // Initial route handling
    const initialHash = window.location.hash.replace("#", "");
    if (initialHash) {
        showView(initialHash);
    } else {
        showView(State.role === "admin" ? "admin-dashboard" : "student-dashboard");
    }

    // Hash change listener
    window.addEventListener("hashchange", () => {
        const newHash = window.location.hash.replace("#", "");
        if (newHash && newHash !== State.activeView) {
            showView(newHash);
        }
    });

    // Close search dropdown on click outside
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".search-container")) {
            const dropdown = document.getElementById("search-results-dropdown");
            if (dropdown) dropdown.classList.remove("active");
        }
    });
});
