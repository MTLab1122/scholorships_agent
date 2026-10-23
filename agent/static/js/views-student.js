/**
 * Student Portal Views
 * Student Opportunity Intelligence Platform
 */

const ViewsStudent = {
    // 1. Student Dashboard
    async renderDashboard() {
        const container = document.getElementById("view-student-dashboard");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading student portal...</div>`;

        try {
            if (!State.currentStudent) {
                const res = await API.getStudents();
                if (res.students && res.students.length > 0) {
                    State.currentStudent = res.students[0];
                }
            }

            const student = State.currentStudent;
            if (!student) {
                container.innerHTML = UI.renderEmptyState(
                    "No Student Profile Active",
                    "Please create or select a student profile to view personalized recommendations and opportunities.",
                    `<button class="btn btn-primary" onclick="showView('student-profile')">Create Student Profile</button>`
                );
                return;
            }

            // Fetch personalized matches and applications
            const matchesRes = await API.getMatches(student.id, 5);
            const matches = matchesRes.matches || [];
            const apps = await API.getApplications(student.id);
            const savedRes = await API.getSavedOpportunities(student.id);
            const saved = savedRes.saved || [];

            container.innerHTML = `
                <!-- Personalized Welcome Banner -->
                <div class="hero-banner" style="margin-bottom: 1.5rem; background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);">
                    <div>
                        <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--primary); font-weight: 700;">Student Portal</div>
                        <h1 class="hero-title">Welcome back, ${student.full_name || student.name}!</h1>
                        <p class="hero-sub">${student.degree_level} in ${student.discipline} • ${student.university} (${student.university_type} sector) • Semester ${student.current_semester} • CGPA ${student.cgpa} • Domicile: ${student.domicile_district || 'Charsadda'}, ${student.domicile_province || 'KP'}</p>
                    </div>
                    <div style="display: flex; gap: 0.75rem;">
                        <button class="btn btn-secondary" onclick="showView('student-profile')">Edit Profile</button>
                        <button class="btn btn-primary" onclick="showView('student-recommendations')">View All Matches &rarr;</button>
                    </div>
                </div>

                <!-- Student Metrics -->
                <div class="metric-grid">
                    ${UI.renderMetricCard("Eligible Matches", matchesRes.total_matches || matches.length, "Based on criteria", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 14 14"/></svg>`)}
                    ${UI.renderMetricCard("Tracked Applications", (apps.applied_count || 0) + (apps.interested_count || 0), "In progress", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`)}
                    ${UI.renderMetricCard("Saved Bookmarks", saved.length, "Opportunities pinned", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>`)}
                    ${UI.renderMetricCard("District Priority", student.domicile_district || "Charsadda", "Priority weighting applied", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`)}
                </div>

                <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem;">
                    <!-- Top Recommended Opportunities -->
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                            <h2 style="font-size: 1.15rem; font-weight: 700; color: var(--text-primary);">Top Ranked Matches For You</h2>
                            <button class="btn btn-outline btn-sm" onclick="showView('student-recommendations')">See All &rarr;</button>
                        </div>
                        ${matches.length === 0 ? UI.renderEmptyState("No immediate matches found", "Try adjusting your profile semester, CGPA, or discipline filters.") : `
                            <div>
                                ${matches.slice(0, 3).map(m => {
                                    const opp = {
                                        id: m.opportunity_id,
                                        name: m.opportunity_name,
                                        sponsor: m.sponsor,
                                        category: m.category,
                                        university_types: m.university_types,
                                        status: m.status,
                                        days_left: m.days_left,
                                        verification_badge: m.verification_badge,
                                        deadline: m.deadline,
                                        benefits: m.benefits,
                                        apply_url: m.apply_url,
                                        charsadda_flag: m.charsadda_flag,
                                        kp_flag: m.kp_flag,
                                        target_uni_flag: m.target_uni_flag
                                    };
                                    return UI.renderOpportunityCard(opp, {
                                        matchScore: m.match_score,
                                        reasons: m.reasons,
                                        unmet_criteria: m.unmet_criteria
                                    });
                                }).join("")}
                            </div>
                        `}
                    </div>

                    <!-- Right Column: Deadlines & Saved -->
                    <div>
                        <div class="card" style="margin-bottom: 1.25rem;">
                            <div class="card-header">
                                <h3 class="card-title">Urgent Approaching Deadlines</h3>
                            </div>
                            <div class="card-body">
                                ${matches.filter(m => m.days_left !== null && m.days_left <= 15).length === 0 ? `
                                    <p style="font-size: 0.85rem; color: var(--text-muted);">No urgent deadlines in the next 15 days.</p>
                                ` : `
                                    <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                                        ${matches.filter(m => m.days_left !== null && m.days_left <= 15).slice(0, 4).map(m => `
                                            <div style="border-bottom: 1px solid var(--border-subtle); padding-bottom: 0.5rem;">
                                                <div style="font-size: 0.85rem; font-weight: 700; color: var(--text-primary);">${m.opportunity_name}</div>
                                                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
                                                    <span style="font-size: 0.75rem; color: var(--danger); font-weight: 600;">${m.days_left} days left</span>
                                                    <button class="btn btn-primary btn-sm" style="font-size: 0.72rem; padding: 2px 6px;" onclick="trackOpportunity('${m.opportunity_id}')">Track</button>
                                                </div>
                                            </div>
                                        `).join("")}
                                    </div>
                                `}
                            </div>
                        </div>

                        <div class="card">
                            <div class="card-header">
                                <h3 class="card-title">My Application Stages</h3>
                                <button class="btn btn-outline btn-sm" onclick="showView('student-applications')">Open Kanban &rarr;</button>
                            </div>
                            <div class="card-body">
                                <div style="display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.82rem;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span>Interested / Evaluating:</span>
                                        <strong>${apps.interested_count || 0}</strong>
                                    </div>
                                    <div style="display: flex; justify-content: space-between;">
                                        <span>Preparing Documents:</span>
                                        <strong>${apps.preparing_count || 0}</strong>
                                    </div>
                                    <div style="display: flex; justify-content: space-between;">
                                        <span>Submitted / Applied:</span>
                                        <strong>${apps.applied_count || 0}</strong>
                                    </div>
                                    <div style="display: flex; justify-content: space-between;">
                                        <span>Accepted / Awarded:</span>
                                        <strong style="color: var(--success);">${apps.awarded_count || 0}</strong>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading student dashboard: ${e.message}</div>`;
        }
    },

    // 2. Student Opportunity Explorer
    async renderOpportunities(filters = {}) {
        const container = document.getElementById("view-student-opportunities");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Searching opportunity catalog...</div>`;

        try {
            const res = await API.getOpportunities(filters);
            const opps = res.opportunities || [];

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">Opportunity Explorer</h1>
                        <p class="page-description">Search verified scholarships, national & international internships, research fellowships, and competitions</p>
                    </div>
                </div>

                <!-- Filter Controls -->
                <div class="filter-bar">
                    <div class="filter-group">
                        <label>Search Opportunities</label>
                        <input type="text" id="student-opp-search" class="form-control" placeholder="Search by name, sponsor, keyword..." value="${filters.search || ''}">
                    </div>
                    <div class="filter-group">
                        <label>Category</label>
                        <select id="student-opp-category" class="form-select">
                            <option value="all">All Opportunities</option>
                            <option value="scholarships" ${filters.category === 'scholarships' ? 'selected' : ''}>Scholarships</option>
                            <option value="internships" ${filters.category === 'internships' ? 'selected' : ''}>Internships</option>
                            <option value="research_fellowships" ${filters.category === 'research_fellowships' ? 'selected' : ''}>Research & Fellowships</option>
                            <option value="competitions_hackathons" ${filters.category === 'competitions_hackathons' ? 'selected' : ''}>Competitions & Hackathons</option>
                            <option value="conferences_exchange" ${filters.category === 'conferences_exchange' ? 'selected' : ''}>Conferences & Exchange</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Semester</label>
                        <select id="student-opp-semester" class="form-select">
                            <option value="">Any Semester</option>
                            ${[1, 2, 3, 4, 5, 6, 7, 8].map(s => `<option value="${s}" ${filters.semester == s ? 'selected' : ''}>Semester ${s}</option>`).join("")}
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>University Sector</label>
                        <select id="student-opp-sector" class="form-select">
                            <option value="all">Public & Private</option>
                            <option value="public" ${filters.university_type === 'public' ? 'selected' : ''}>Public Universities</option>
                            <option value="private" ${filters.university_type === 'private' ? 'selected' : ''}>Private Universities</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Status</label>
                        <select id="student-opp-status" class="form-select">
                            <option value="all">All</option>
                            <option value="Open" ${filters.status === 'Open' ? 'selected' : ''}>Open Only</option>
                            <option value="Closing soon" ${filters.status === 'Closing soon' ? 'selected' : ''}>Closing Soon</option>
                        </select>
                    </div>
                    <div>
                        <button class="btn btn-primary" onclick="applyStudentOppFilters()">Search</button>
                    </div>
                </div>

                <!-- Opportunities List -->
                ${opps.length === 0 ? UI.renderEmptyState("No opportunities found", "Try loosening your search filters.") : `
                    <div>
                        ${opps.map(o => UI.renderOpportunityCard(o)).join("")}
                    </div>
                `}
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading opportunities: ${e.message}</div>`;
        }
    },

    // 3. Personalized Recommendations
    async renderRecommendations() {
        const container = document.getElementById("view-student-recommendations");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Analyzing personalized recommendations...</div>`;

        try {
            const student = State.currentStudent;
            if (!student) {
                container.innerHTML = UI.renderEmptyState("No Student Profile Active", "Please select or create your student profile.", `<button class="btn btn-primary" onclick="showView('student-profile')">Setup Profile</button>`);
                return;
            }

            const res = await API.getMatches(student.id, 30);
            const matches = res.matches || [];

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">Personalized Opportunity Recommendations</h1>
                        <p class="page-description">Ranked matches evaluated against your degree (${student.discipline}), semester (${student.current_semester}), CGPA (${student.cgpa}), sector (${student.university_type}), and district (${student.domicile_district || 'Charsadda'})</p>
                    </div>
                    <div class="header-actions">
                        <button class="btn btn-secondary" onclick="ViewsStudent.renderRecommendations()">Refresh Recommendations</button>
                    </div>
                </div>

                ${matches.length === 0 ? UI.renderEmptyState("No matching opportunities found", "No schemes matched your exact semester or GPA criteria. You can review all opportunities in the Explorer.") : `
                    <div>
                        ${matches.map(m => {
                            const opp = {
                                id: m.opportunity_id,
                                name: m.opportunity_name,
                                sponsor: m.sponsor,
                                category: m.category,
                                university_types: m.university_types,
                                status: m.status,
                                days_left: m.days_left,
                                verification_badge: m.verification_badge,
                                deadline: m.deadline,
                                benefits: m.benefits,
                                apply_url: m.apply_url,
                                charsadda_flag: m.charsadda_flag,
                                kp_flag: m.kp_flag,
                                target_uni_flag: m.target_uni_flag
                            };
                            return UI.renderOpportunityCard(opp, {
                                matchScore: m.match_score,
                                reasons: m.reasons,
                                unmet_criteria: m.unmet_criteria
                            });
                        }).join("")}
                    </div>
                `}
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading recommendations: ${e.message}</div>`;
        }
    },

    // 4. Saved Opportunities
    async renderSaved() {
        const container = document.getElementById("view-student-saved");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading bookmarked opportunities...</div>`;

        try {
            const student = State.currentStudent;
            if (!student) {
                container.innerHTML = UI.renderEmptyState("Profile Needed", "Please select a student profile.");
                return;
            }

            const res = await API.getSavedOpportunities(student.id);
            const saved = res.saved || [];

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">Saved Opportunities Bookmarks</h1>
                        <p class="page-description">Opportunities you have bookmarked for easy follow-up and application (${saved.length} saved)</p>
                    </div>
                </div>

                ${saved.length === 0 ? UI.renderEmptyState("No Saved Opportunities", "Bookmark opportunities from the Explorer or Recommendations to review them here.", `<button class="btn btn-primary" onclick="showView('student-opportunities')">Browse Opportunities</button>`) : `
                    <div>
                        ${saved.map(o => UI.renderOpportunityCard(o)).join("")}
                    </div>
                `}
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading saved: ${e.message}</div>`;
        }
    },

    // 5. My Applications (Kanban Board)
    async renderApplications() {
        const container = document.getElementById("view-student-applications");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading application tracker...</div>`;

        try {
            const student = State.currentStudent;
            if (!student) return;

            const kanbanData = await API.getApplications(student.id);
            const columns = kanbanData.columns || {};

            const columnKeys = [
                { id: "interested", title: "Interested" },
                { id: "checking_eligibility", title: "Checking Eligibility" },
                { id: "preparing_documents", title: "Preparing Documents" },
                { id: "ready_to_apply", title: "Ready to Apply" },
                { id: "applied", title: "Applied / Submitted" },
                { id: "interview", title: "Interview / Assessment" },
                { id: "awarded", title: "Awarded / Accepted" },
                { id: "rejected", title: "Rejected" },
                { id: "withdrawn", title: "Withdrawn" }
            ];

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">Application Kanban Tracker</h1>
                        <p class="page-description">Track your opportunity applications through each stage of the lifecycle</p>
                    </div>
                </div>

                <div class="kanban-board">
                    ${columnKeys.map(col => {
                        const items = columns[col.id] || [];
                        return `
                            <div class="kanban-col">
                                <div class="kanban-header">
                                    <span class="kanban-title">${col.title}</span>
                                    <span class="badge badge-public">${items.length}</span>
                                </div>
                                <div style="flex:1;">
                                    ${items.map(app => `
                                        <div class="kanban-card">
                                            <div class="kanban-opp-name">${app.opportunity_name || "Opportunity"}</div>
                                            <div class="kanban-sponsor">${app.sponsor || ""}</div>
                                            ${app.deadline ? `<div style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 0.5rem;">Deadline: <strong>${app.deadline}</strong></div>` : ""}
                                            
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem; pt: 0.5rem; border-top: 1px solid var(--border-subtle); padding-top: 0.5rem;">
                                                <select class="form-select btn-sm" style="font-size: 0.72rem; height: 26px; padding: 0 4px;" onchange="moveApplicationStatus('${app.id}', this.value)">
                                                    <option value="" disabled selected>Move to...</option>
                                                    ${columnKeys.map(c => `<option value="${c.id}">${c.title}</option>`).join("")}
                                                </select>
                                                <button class="btn btn-outline btn-sm" style="font-size: 0.72rem; padding: 2px 6px;" onclick="openPrepWorkspace('${app.opportunity_id}')">Prep</button>
                                            </div>
                                        </div>
                                    `).join("")}
                                </div>
                            </div>
                        `;
                    }).join("")}
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading applications: ${e.message}</div>`;
        }
    },

    // 6. Application Preparation Studio Workspace
    async renderPrepWorkspace(oppId) {
        const student = State.currentStudent;
        if (!student) {
            UI.showToast("Student profile required", "error");
            return;
        }

        UI.showToast("Generating personalized application preparation packet...", "info");
        try {
            const packet = await API.getPrepPacket(student.id, oppId);

            const body = `
                <div style="display: flex; flex-direction: column; gap: 1.25rem;">
                    <div>
                        <h4 style="font-size: 1.1rem; color: var(--text-primary);">${packet.opportunity_name}</h4>
                        <div style="font-size: 0.85rem; color: var(--text-muted);">${packet.sponsor}</div>
                    </div>

                    <!-- Required Documents Checklist -->
                    <div class="card" style="margin-bottom: 0;">
                        <div class="card-header"><h4 class="card-title">Attested Document Requirements</h4></div>
                        <div class="card-body">
                            <ul style="margin-left: 1.2rem; font-size: 0.85rem; display: flex; flex-direction: column; gap: 4px;">
                                ${(packet.documents_checklist || []).map(doc => `<li>${doc}</li>`).join("") || `<li>Standard attested academic transcripts, CNIC/B-Form, and Domicile Certificate.</li>`}
                            </ul>
                        </div>
                    </div>

                    <!-- Statement of Purpose (SOP) / Essay Prompts -->
                    <div class="card" style="margin-bottom: 0;">
                        <div class="card-header"><h4 class="card-title">Statement of Purpose (SOP) Guidelines</h4></div>
                        <div class="card-body">
                            <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; white-space: pre-wrap;">${packet.sop_outline || packet.sop_guidelines || "Highlight your academic standing, district background, leadership contributions, and exact alignment with this program's mission."}</p>
                        </div>
                    </div>

                    <!-- Recommendation Letter Request Template -->
                    <div class="card" style="margin-bottom: 0;">
                        <div class="card-header"><h4 class="card-title">Recommendation Letter Request Template</h4></div>
                        <div class="card-body">
                            <textarea class="form-control" style="height: 120px; font-size: 0.82rem; font-family: var(--font-mono);" readonly>${packet.recommendation_template || "Dear Professor,\n\nI am applying for the opportunity..."}</textarea>
                            <button class="btn btn-outline btn-sm" style="margin-top: 0.5rem;" onclick="copyToClipboard(this.previousElementSibling.value)">Copy Template</button>
                        </div>
                    </div>
                </div>
            `;

            const footer = `
                <button class="btn btn-outline" onclick="UI.closeDrawer()">Close</button>
                <button class="btn btn-primary" onclick="trackOpportunity('${oppId}'); UI.closeDrawer();">Track Application</button>
            `;

            UI.openDrawer("Application Preparation Studio", body, footer);
        } catch (e) {
            UI.showToast(`Failed to generate prep packet: ${e.message}`, "error");
        }
    },

    // 7. Student Profile Editor
    async renderProfile() {
        const container = document.getElementById("view-student-profile");
        const student = State.currentStudent || {
            full_name: "Muhammad Talha",
            email: "student@example.com",
            phone: "+92 300 1234567",
            university: "University of Peshawar",
            university_type: "public",
            degree_level: "Undergraduate",
            discipline: "Computer Science",
            current_semester: 4,
            cgpa: 3.4,
            domicile_district: "Charsadda",
            domicile_province: "Khyber Pakhtunkhwa",
            funding_need: "medium",
            work_preference: "any"
        };

        container.innerHTML = `
            <div class="page-header">
                <div>
                    <h1 class="page-title">Student Profile & Academic Criteria</h1>
                    <p class="page-description">Configure your university standing, degree level, semester, CGPA, and domicile for transparent matching</p>
                </div>
                <div class="header-actions">
                    <button class="btn btn-primary" onclick="saveStudentProfileForm()">Save Profile & Run Matching</button>
                </div>
            </div>

            <div class="card" style="max-width: 800px;">
                <div class="card-body">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div class="form-group">
                            <label class="form-label">Full Name</label>
                            <input type="text" id="prof-name" class="form-control" value="${student.full_name || student.name || ''}">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Email Address</label>
                            <input type="email" id="prof-email" class="form-control" value="${student.email || ''}">
                        </div>
                        <div class="form-group">
                            <label class="form-label">University</label>
                            <input type="text" id="prof-uni" class="form-control" value="${student.university || 'University of Peshawar'}">
                        </div>
                        <div class="form-group">
                            <label class="form-label">University Sector</label>
                            <select id="prof-sector" class="form-select">
                                <option value="public" ${student.university_type === 'public' ? 'selected' : ''}>Public Sector</option>
                                <option value="private" ${student.university_type === 'private' ? 'selected' : ''}>Private Sector</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Degree Level</label>
                            <select id="prof-degree" class="form-select">
                                <option value="Undergraduate" ${student.degree_level === 'Undergraduate' ? 'selected' : ''}>Undergraduate (BS / BE)</option>
                                <option value="Postgraduate" ${student.degree_level === 'Postgraduate' ? 'selected' : ''}>Postgraduate (MS / MPhil)</option>
                                <option value="PhD" ${student.degree_level === 'PhD' ? 'selected' : ''}>PhD / Doctoral</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Discipline / Major</label>
                            <input type="text" id="prof-discipline" class="form-control" value="${student.discipline || 'Computer Science'}">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Current Semester (1 - 8+)</label>
                            <input type="number" id="prof-semester" class="form-control" min="1" max="12" value="${student.current_semester || 4}">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Cumulative GPA (CGPA)</label>
                            <input type="number" id="prof-cgpa" class="form-control" min="1.0" max="4.0" step="0.01" value="${student.cgpa || 3.2}">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Domicile District</label>
                            <input type="text" id="prof-district" class="form-control" value="${student.domicile_district || 'Charsadda'}">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Domicile Province</label>
                            <input type="text" id="prof-province" class="form-control" value="${student.domicile_province || 'Khyber Pakhtunkhwa'}">
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    // 8. Notifications Center
    async renderNotifications() {
        const container = document.getElementById("view-notifications");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading notifications...</div>`;

        try {
            await State.refreshNotifications();
            const notifications = State.notifications;

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">Notification Center</h1>
                        <p class="page-description">Approaching deadline alerts, new opportunity matches, and administrative updates</p>
                    </div>
                    <div class="header-actions">
                        <button class="btn btn-outline" onclick="markAllNotificationsAsRead()">Mark All Read</button>
                    </div>
                </div>

                ${notifications.length === 0 ? UI.renderEmptyState("No notifications", "You are completely caught up on all opportunity alerts.") : `
                    <div class="card">
                        <div class="card-body" style="padding: 0;">
                            <div style="display: flex; flex-direction: column;">
                                ${notifications.map(n => `
                                    <div style="padding: 1rem 1.25rem; border-bottom: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: flex-start; background: ${n.read_at ? 'transparent' : 'var(--bg-surface)'};">
                                        <div>
                                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 4px;">
                                                <span class="badge ${n.notification_type === 'deadline' ? 'badge-closing' : 'badge-public'}">${n.notification_type}</span>
                                                <strong style="font-size: 0.9rem; color: var(--text-primary);">${n.title}</strong>
                                                ${!n.read_at ? `<span style="width: 8px; height: 8px; border-radius: 50%; background: var(--primary);"></span>` : ""}
                                            </div>
                                            <p style="font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 4px;">${n.message}</p>
                                            <div style="font-size: 0.72rem; color: var(--text-muted);">${n.sent_at ? n.sent_at.slice(0, 19).replace('T', ' ') : ''}</div>
                                        </div>
                                        <div>
                                            ${!n.read_at ? `<button class="btn btn-outline btn-sm" onclick="markNotificationSingleRead(${n.id})">Mark Read</button>` : ""}
                                        </div>
                                    </div>
                                `).join("")}
                            </div>
                        </div>
                    </div>
                `}
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading notifications: ${e.message}</div>`;
        }
    }
};

window.ViewsStudent = ViewsStudent;
