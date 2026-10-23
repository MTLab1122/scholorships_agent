/**
 * Admin Control Center Views
 * Student Opportunity Intelligence Platform
 */

const ViewsAdmin = {
    // 1. Admin Dashboard
    async renderDashboard() {
        const container = document.getElementById("view-admin-dashboard");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading live dashboard metrics...</div>`;

        try {
            const metrics = await API.getAdminMetrics();
            const telemetry = await API.getOrchestratorStatus();

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">Admin Control Center</h1>
                        <p class="page-description">Autonomous Multi-Agent Opportunity Intelligence Platform Monitoring & Orchestration</p>
                    </div>
                    <div class="header-actions">
                        <button class="btn btn-secondary" onclick="ViewsAdmin.renderDashboard()">Refresh</button>
                        <button class="btn btn-outline" onclick="triggerDeadlineScan()">Scan Deadlines</button>
                        <button class="btn btn-primary" onclick="triggerFullPipeline()">Run Master Orchestrator</button>
                    </div>
                </div>

                <!-- KPI Metric Grid -->
                <div class="metric-grid">
                    ${UI.renderMetricCard("Total Opportunities", metrics.total_opportunities, "Active & Cataloged", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>`)}
                    ${UI.renderMetricCard("Open Opportunities", metrics.open_opportunities, `${metrics.closing_soon} closing soon`, `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 14 14"/></svg>`)}
                    ${UI.renderMetricCard("Scholarships", metrics.scholarships_count, "National & International", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 2 2 3 6 3s6-1 6-3v-5"/></svg>`)}
                    ${UI.renderMetricCard("Internships", metrics.internships_count, "Domestic & Global", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>`)}
                    ${UI.renderMetricCard("Awaiting Verification", metrics.unverified_count, "Pending Review", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`)}
                    ${UI.renderMetricCard("Upcoming Deadlines", metrics.upcoming_deadlines, "<= 30 days left", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`)}
                    ${UI.renderMetricCard("Students Registered", metrics.total_students, "Profiles active", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`)}
                    ${UI.renderMetricCard("Reports Generated", metrics.total_reports, "PDF, XLSX, CSV, HTML", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`)}
                </div>

                <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem;">
                    <!-- Opportunity Category & Sector Breakdown -->
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Catalog Distribution by Category</h3>
                        </div>
                        <div class="card-body">
                            <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                                ${Object.entries(metrics.category_distribution || {}).map(([cat, count]) => {
                                    const pct = Math.round((count / (metrics.total_opportunities || 1)) * 100);
                                    return `
                                        <div>
                                            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px;">
                                                <span style="text-transform: capitalize; font-weight: 600;">${cat}</span>
                                                <span style="color: var(--text-muted);">${count} (${pct}%)</span>
                                            </div>
                                            <div style="width: 100%; height: 8px; background: var(--bg-surface); border-radius: 4px; overflow: hidden;">
                                                <div style="width: ${pct}%; height: 100%; background: var(--primary);"></div>
                                            </div>
                                        </div>
                                    `;
                                }).join("")}
                            </div>
                        </div>
                    </div>

                    <!-- Sector & Scope Breakdown -->
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Sector & Scope Intelligence</h3>
                        </div>
                        <div class="card-body">
                            <div style="margin-bottom: 1rem;">
                                <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700; margin-bottom: 0.5rem;">University Sector</div>
                                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                                    <span class="badge badge-public">Public: ${metrics.university_type_distribution.public || 0}</span>
                                    <span class="badge badge-private">Private: ${metrics.university_type_distribution.private || 0}</span>
                                    <span class="badge badge-open">Both Sectors: ${metrics.university_type_distribution.both || 0}</span>
                                </div>
                            </div>
                            <div style="margin-bottom: 1rem;">
                                <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700; margin-bottom: 0.5rem;">Geographic Scope</div>
                                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                                    <span class="badge badge-kp">National: ${metrics.scope_distribution.national}</span>
                                    <span class="badge badge-charsadda">International: ${metrics.scope_distribution.international}</span>
                                </div>
                            </div>
                            <div>
                                <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700; margin-bottom: 0.5rem;">Source Registry Health</div>
                                <p style="font-size: 0.85rem; color: var(--text-secondary);">
                                    ${metrics.total_sources} registered portals • 
                                    <strong style="color: ${metrics.sources_attention > 0 ? 'var(--danger)' : 'var(--success)'};">${metrics.sources_attention} need attention</strong>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Jobs and Changes -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Recent Autonomous Workflow Runs</h3>
                        <button class="btn btn-outline btn-sm" onclick="showView('admin-workflows')">View All Runs &rarr;</button>
                    </div>
                    <div class="card-body" style="padding: 0;">
                        <div class="table-responsive">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Run ID</th>
                                        <th>Agent / Job</th>
                                        <th>Status</th>
                                        <th>Started</th>
                                        <th>Discovered</th>
                                        <th>Extracted</th>
                                        <th>Verified</th>
                                        <th>Summary</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${(telemetry.recent_jobs || []).slice(0, 5).map(j => `
                                        <tr>
                                            <td><code>${j.id.slice(0, 8)}</code></td>
                                            <td><strong>${j.agent_name}</strong></td>
                                            <td><span class="badge ${j.status === 'completed' || j.status === 'SUCCESS' ? 'badge-confirmed' : 'badge-closing'}">${j.status}</span></td>
                                            <td>${j.started_at ? j.started_at.slice(0, 19).replace('T', ' ') : '-'}</td>
                                            <td>${j.items_discovered || 0}</td>
                                            <td>${j.items_extracted || 0}</td>
                                            <td>${j.items_verified || 0}</td>
                                            <td>${j.log_summary || '-'}</td>
                                        </tr>
                                    `).join("") || `<tr><td colspan="8" style="text-align:center; padding: 2rem;">No recent jobs recorded.</td></tr>`}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading admin dashboard: ${e.message}</div>`;
        }
    },

    // 2. AI Agent Management Center
    async renderAgents() {
        const container = document.getElementById("view-admin-agents");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading AI Agents catalog...</div>`;

        try {
            const res = await API.getAgents();
            const agents = res.agents || [];

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">AI Agent Management Center</h1>
                        <p class="page-description">Configure, inspect, and trigger the 15 specialized autonomous intelligence agents</p>
                    </div>
                    <div class="header-actions">
                        <button class="btn btn-primary" onclick="triggerFullPipeline()">Trigger Master Orchestrator</button>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.25rem;">
                    ${agents.map(a => `
                        <div class="card" style="margin-bottom: 0;">
                            <div class="card-header">
                                <div>
                                    <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary);">${a.name}</h4>
                                    <div style="font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-mono);">${a.id}</div>
                                </div>
                                <span class="badge ${a.status === 'operational' ? 'badge-confirmed' : 'badge-closing'}">${a.status}</span>
                            </div>
                            <div class="card-body">
                                <p style="font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 0.75rem; min-height: 48px;">${a.description || a.purpose}</p>
                                <div style="display: flex; flex-direction: column; gap: 4px; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 1rem; background: var(--bg-surface); padding: 0.5rem; border-radius: 4px;">
                                    <div>Provider / Engine: <strong>${a.model || "Deterministic / Gemini"}</strong></div>
                                    <div>Last Execution: <strong>${a.last_run ? a.last_run.slice(0, 19).replace('T', ' ') : 'Ready'}</strong></div>
                                    <div>Failures: <strong>${a.failure_count || 0}</strong></div>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <button class="btn btn-outline btn-sm" onclick="ViewsAdmin.viewAgentDetails('${a.id}')">Inspect Agent</button>
                                    <button class="btn btn-primary btn-sm" onclick="ViewsAdmin.runIndividualAgent('${a.id}')">Run Now</button>
                                </div>
                            </div>
                        </div>
                    `).join("")}
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading agents: ${e.message}</div>`;
        }
    },

    async viewAgentDetails(agentId) {
        try {
            const res = await API.getAgents();
            const agent = (res.agents || []).find(a => a.id === agentId);
            if (!agent) return;

            const body = `
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    <div>
                        <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700;">Role & Responsibilities</div>
                        <p style="font-size: 0.88rem; color: var(--text-primary); margin-top: 4px;">${agent.description || agent.purpose}</p>
                    </div>
                    <div style="background: var(--bg-surface); padding: 0.75rem; border-radius: var(--radius-md);">
                        <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700; margin-bottom: 4px;">Operational Telemetry</div>
                        <div style="font-size: 0.8rem; display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                            <div>Status: <strong>${agent.status}</strong></div>
                            <div>Execution Mode: <strong>${agent.model}</strong></div>
                            <div>Failure Count: <strong>${agent.failure_count || 0}</strong></div>
                            <div>Last Run: <strong>${agent.last_run || "None"}</strong></div>
                        </div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700;">Supported Actions</div>
                        <ul style="font-size: 0.82rem; margin-left: 1.2rem; margin-top: 4px;">
                            ${(agent.supported_actions || ["run", "view_logs"]).map(act => `<li>${act}</li>`).join("")}
                        </ul>
                    </div>
                </div>
            `;
            const footer = `
                <button class="btn btn-outline" onclick="UI.closeDrawer()">Close</button>
                <button class="btn btn-primary" onclick="ViewsAdmin.runIndividualAgent('${agent.id}'); UI.closeDrawer();">Run Agent Now</button>
            `;
            UI.openDrawer(`Agent: ${agent.name}`, body, footer);
        } catch (e) {
            UI.showToast(`Failed to load agent: ${e.message}`, "error");
        }
    },

    async runIndividualAgent(agentId) {
        UI.showToast(`Triggering execution for agent: ${agentId}...`, "info");
        try {
            const res = await API.runAgent(agentId);
            UI.showToast(`Agent execution started: ${res.status || 'OK'}`, "success");
            this.renderAgents();
        } catch (e) {
            UI.showToast(`Agent run failed: ${e.message}`, "error");
        }
    },

    // 3. Workflow Orchestration Center
    async renderWorkflows() {
        const container = document.getElementById("view-admin-workflows");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading workflow orchestration pipeline...</div>`;

        try {
            const telemetry = await API.getOrchestratorStatus();
            const jobs = telemetry.recent_jobs || [];

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">Workflow Orchestration Center</h1>
                        <p class="page-description">Autonomous Pipeline Execution Flow: Discovery &rarr; Extraction &rarr; Verification &rarr; Reporting &rarr; Notification</p>
                    </div>
                    <div class="header-actions">
                        <button class="btn btn-primary" onclick="triggerFullPipeline()">Trigger Manual Workflow Run</button>
                    </div>
                </div>

                <!-- Visual Pipeline Flow Diagram -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Autonomous Opportunity Pipeline State Machine</h3>
                    </div>
                    <div class="card-body">
                        <div class="workflow-pipeline">
                            <div class="workflow-step completed">1. Discovery</div>
                            <span class="workflow-arrow">&rarr;</span>
                            <div class="workflow-step completed">2. Extraction</div>
                            <span class="workflow-arrow">&rarr;</span>
                            <div class="workflow-step completed">3. Classification</div>
                            <span class="workflow-arrow">&rarr;</span>
                            <div class="workflow-step completed">4. Verification</div>
                            <span class="workflow-arrow">&rarr;</span>
                            <div class="workflow-step completed">5. Deduplication</div>
                            <span class="workflow-arrow">&rarr;</span>
                            <div class="workflow-step completed">6. Semester Matching</div>
                            <span class="workflow-arrow">&rarr;</span>
                            <div class="workflow-step completed">7. 20-Report Gen</div>
                            <span class="workflow-arrow">&rarr;</span>
                            <div class="workflow-step completed">8. Notification</div>
                        </div>
                        <p style="font-size: 0.8rem; color: var(--text-muted);">
                            The Master Orchestrator coordinates these stages deterministically, ensuring that unverified, expired, or unsupported claims are rejected before publication reports are compiled.
                        </p>
                    </div>
                </div>

                <!-- Execution History Table -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Workflow Execution History</h3>
                    </div>
                    <div class="card-body" style="padding: 0;">
                        <div class="table-responsive">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Job ID</th>
                                        <th>Agent / Job</th>
                                        <th>Run Type</th>
                                        <th>Status</th>
                                        <th>Started</th>
                                        <th>Items Discovered</th>
                                        <th>Items Extracted</th>
                                        <th>Items Verified</th>
                                        <th>Summary / Log</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${jobs.map(j => `
                                        <tr>
                                            <td><code>${j.id.slice(0, 8)}</code></td>
                                            <td><strong>${j.agent_name}</strong></td>
                                            <td><span class="badge badge-public">${j.run_type || 'manual'}</span></td>
                                            <td><span class="badge ${j.status === 'completed' || j.status === 'SUCCESS' ? 'badge-confirmed' : 'badge-closing'}">${j.status}</span></td>
                                            <td>${j.started_at ? j.started_at.slice(0, 19).replace('T', ' ') : '-'}</td>
                                            <td>${j.items_discovered || 0}</td>
                                            <td>${j.items_extracted || 0}</td>
                                            <td>${j.items_verified || 0}</td>
                                            <td>${j.log_summary || '-'}</td>
                                        </tr>
                                    `).join("") || `<tr><td colspan="9" style="text-align:center; padding: 2rem;">No workflow runs recorded yet.</td></tr>`}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading workflows: ${e.message}</div>`;
        }
    },

    // 4. Opportunity Management Center
    async renderOpportunities(filters = {}) {
        const container = document.getElementById("view-admin-opportunities");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading opportunities catalog...</div>`;

        try {
            const res = await API.getOpportunities(filters);
            const opps = res.opportunities || [];
            const total = res.total_matches || opps.length;

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">Opportunity Management Center</h1>
                        <p class="page-description">Search, filter, inspect evidence, and manage verified opportunities (${total} records found)</p>
                    </div>
                    <div class="header-actions">
                        <button class="btn btn-secondary" onclick="exportFilteredOpportunities()">Export CSV</button>
                    </div>
                </div>

                <!-- Comprehensive Filters -->
                <div class="filter-bar">
                    <div class="filter-group">
                        <label>Search</label>
                        <input type="text" id="admin-opp-search" class="form-control" placeholder="Search title, sponsor, field..." value="${filters.search || ''}">
                    </div>
                    <div class="filter-group">
                        <label>Category</label>
                        <select id="admin-opp-category" class="form-select">
                            <option value="all">All Categories</option>
                            <option value="scholarships" ${filters.category === 'scholarships' ? 'selected' : ''}>Scholarships</option>
                            <option value="internships" ${filters.category === 'internships' ? 'selected' : ''}>Internships</option>
                            <option value="research_fellowships" ${filters.category === 'research_fellowships' ? 'selected' : ''}>Research & Fellowships</option>
                            <option value="competitions_hackathons" ${filters.category === 'competitions_hackathons' ? 'selected' : ''}>Competitions & Hackathons</option>
                            <option value="conferences_exchange" ${filters.category === 'conferences_exchange' ? 'selected' : ''}>Conferences & Exchange</option>
                            <option value="jobs_graduate_programs" ${filters.category === 'jobs_graduate_programs' ? 'selected' : ''}>Jobs & Graduate Programs</option>
                            <option value="free_learning_certifications" ${filters.category === 'free_learning_certifications' ? 'selected' : ''}>Free Learning</option>
                            <option value="entrepreneurship_startups" ${filters.category === 'entrepreneurship_startups' ? 'selected' : ''}>Startups & Incubators</option>
                            <option value="community_leadership" ${filters.category === 'community_leadership' ? 'selected' : ''}>Community & Leadership</option>
                            <option value="fyp_industry_projects" ${filters.category === 'fyp_industry_projects' ? 'selected' : ''}>Final-Year Projects (FYP)</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Sector</label>
                        <select id="admin-opp-sector" class="form-select">
                            <option value="all">All Sectors</option>
                            <option value="public" ${filters.university_type === 'public' ? 'selected' : ''}>Public Sector</option>
                            <option value="private" ${filters.university_type === 'private' ? 'selected' : ''}>Private Sector</option>
                            <option value="both" ${filters.university_type === 'both' ? 'selected' : ''}>Both Sectors</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Semester</label>
                        <select id="admin-opp-semester" class="form-select">
                            <option value="">Any Semester</option>
                            ${[1, 2, 3, 4, 5, 6, 7, 8].map(s => `<option value="${s}" ${filters.semester == s ? 'selected' : ''}>Semester ${s}</option>`).join("")}
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Status</label>
                        <select id="admin-opp-status" class="form-select">
                            <option value="all">All Statuses</option>
                            <option value="Open" ${filters.status === 'Open' ? 'selected' : ''}>Open</option>
                            <option value="Closing soon" ${filters.status === 'Closing soon' ? 'selected' : ''}>Closing Soon</option>
                            <option value="Closed" ${filters.status === 'Closed' ? 'selected' : ''}>Closed / Expired</option>
                        </select>
                    </div>
                    <div>
                        <button class="btn btn-primary" onclick="applyAdminOppFilters()">Apply Filters</button>
                        <button class="btn btn-outline" onclick="resetAdminOppFilters()">Reset</button>
                    </div>
                </div>

                <!-- Opportunities Table -->
                <div class="card">
                    <div class="card-body" style="padding: 0;">
                        <div class="table-responsive">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Opportunity Title</th>
                                        <th>Sponsor / Provider</th>
                                        <th>Category</th>
                                        <th>Sector</th>
                                        <th>Status</th>
                                        <th>Deadline</th>
                                        <th>Verification</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${opps.map(o => `
                                        <tr>
                                            <td>
                                                <div style="font-weight: 700; color: var(--text-primary);">${o.name}</div>
                                                <div style="font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-mono);">${o.id}</div>
                                            </td>
                                            <td>${o.sponsor}</td>
                                            <td><span style="text-transform: capitalize;">${o.category || 'other'}</span></td>
                                            <td>${UI.renderSectorBadge(o.university_types)}</td>
                                            <td>${UI.renderStatusBadge(o.status, o.days_left)}</td>
                                            <td>${o.deadline || 'not stated'}</td>
                                            <td>${UI.renderVerificationBadge(o.verification_badge, o.source_trust_tier)}</td>
                                            <td>
                                                <button class="btn btn-outline btn-sm" onclick="openOpportunityDetail('${o.id}')">Inspect</button>
                                            </td>
                                        </tr>
                                    `).join("") || `<tr><td colspan="8" style="text-align:center; padding: 2rem;">No opportunities matched your filters.</td></tr>`}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading opportunities: ${e.message}</div>`;
        }
    },

    // 5. Verification and Review Queue
    async renderVerificationQueue() {
        const container = document.getElementById("view-admin-verification");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading verification review queue...</div>`;

        try {
            const queue = await API.getVerificationQueue(50);

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">Verification & Quality Control Queue</h1>
                        <p class="page-description">Review unconfirmed, flagged, or disputed opportunities side-by-side with official source evidence (${queue.length} items awaiting review)</p>
                    </div>
                    <div class="header-actions">
                        <button class="btn btn-secondary" onclick="ViewsAdmin.renderVerificationQueue()">Refresh Queue</button>
                    </div>
                </div>

                ${queue.length === 0 ? UI.renderEmptyState("Verification Queue Clear", "No suspicious or unverified opportunities currently pending administrative review.") : `
                    <div style="display: flex; flex-direction: column; gap: 1rem;">
                        ${queue.map(item => `
                            <div class="card" id="queue-item-${item.id}">
                                <div class="card-header">
                                    <div>
                                        <h3 class="card-title">${item.name}</h3>
                                        <div style="font-size: 0.8rem; color: var(--text-muted);">${item.sponsor} • Category: ${item.category}</div>
                                    </div>
                                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                                        ${item.fraud_risk_score > 0 ? `<span class="badge" style="background: rgba(239,68,68,0.15); color: #DC2626;">Fraud Risk Score: ${item.fraud_risk_score}</span>` : ""}
                                        ${UI.renderVerificationBadge(item.verification_badge, item.source_trust_tier)}
                                    </div>
                                </div>
                                <div class="card-body">
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                                        <!-- Extracted Details Panel -->
                                        <div style="background: var(--bg-surface); padding: 1rem; border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
                                            <div style="font-size: 0.72rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700; margin-bottom: 0.5rem;">Extracted Opportunity Attributes</div>
                                            <div style="font-size: 0.82rem; display: flex; flex-direction: column; gap: 4px;">
                                                <div>Deadline: <strong>${item.deadline}</strong> (${item.days_left !== null ? item.days_left + 'd left' : 'no date'})</div>
                                                <div>Sector: <strong>${item.university_types}</strong></div>
                                                <div>Apply URL: <a href="${item.apply_url}" target="_blank" rel="noopener noreferrer" style="color: var(--primary);">${item.apply_url}</a></div>
                                                <div>Apply Link HTTP Status: <strong>${item.link_status_apply || 'Unchecked'}</strong></div>
                                            </div>
                                        </div>

                                        <!-- Official Source Evidence Quote -->
                                        <div style="background: var(--bg-surface); padding: 1rem; border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
                                            <div style="font-size: 0.72rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700; margin-bottom: 0.5rem;">Official Source Evidence Excerpt</div>
                                            <blockquote style="font-size: 0.82rem; color: var(--text-secondary); font-style: italic; border-left: 3px solid var(--primary); padding-left: 0.75rem;">
                                                "${item.evidence_quote && item.evidence_quote !== 'not stated' ? item.evidence_quote : 'No verbatim evidence snippet recorded.'}"
                                            </blockquote>
                                            <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">
                                                Source URL: <a href="${item.source_url}" target="_blank" rel="noopener noreferrer" style="color: var(--primary);">${item.source_url}</a>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Action Bar -->
                                    <div style="display: flex; justify-content: flex-end; gap: 0.75rem; border-top: 1px solid var(--border-subtle); padding-top: 0.75rem;">
                                        <button class="btn btn-danger btn-sm" onclick="reviewVerificationDecision('${item.id}', 'reject')">Reject & Flag</button>
                                        <button class="btn btn-outline btn-sm" onclick="openOpportunityDetail('${item.id}')">Edit Attributes</button>
                                        <button class="btn btn-primary btn-sm" onclick="reviewVerificationDecision('${item.id}', 'approve')">Approve as Verified</button>
                                    </div>
                                </div>
                            </div>
                        `).join("")}
                    </div>
                `}
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading verification queue: ${e.message}</div>`;
        }
    },

    // 6. Source Registry
    async renderSources() {
        const container = document.getElementById("view-admin-sources");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading source registry...</div>`;

        try {
            const res = await API.getSources();
            const sources = res.sources || [];

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">Source Registry & Research Controls</h1>
                        <p class="page-description">Manage authoritative university portals, HEC feeds, government departments, and educational websites</p>
                    </div>
                    <div class="header-actions">
                        <button class="btn btn-primary" onclick="openAddSourceModal()">+ Add New Source</button>
                    </div>
                </div>

                <div class="card">
                    <div class="card-body" style="padding: 0;">
                        <div class="table-responsive">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Source Name</th>
                                        <th>URL / Domain</th>
                                        <th>Trust Tier</th>
                                        <th>Category</th>
                                        <th>Status</th>
                                        <th>Items Discovered</th>
                                        <th>Last Checked</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${sources.map(s => `
                                        <tr>
                                            <td><strong>${s.name}</strong></td>
                                            <td><a href="${s.url}" target="_blank" rel="noopener noreferrer" style="color: var(--primary); font-size: 0.8rem;">${s.url}</a></td>
                                            <td><span class="badge ${s.tier === 1 ? 'badge-confirmed' : 'badge-public'}">Tier ${s.tier}</span></td>
                                            <td><span style="text-transform: capitalize;">${s.category}</span></td>
                                            <td><span class="badge ${s.status === 'active' ? 'badge-open' : 'badge-closed'}">${s.status}</span></td>
                                            <td><strong>${s.items_discovered || 0}</strong></td>
                                            <td>${s.last_checked ? s.last_checked.slice(0, 19).replace('T', ' ') : 'Pending'}</td>
                                            <td>
                                                <button class="btn btn-outline btn-sm" onclick="testSourceConnectivity('${s.url}')">Test</button>
                                            </td>
                                        </tr>
                                    `).join("") || `<tr><td colspan="8" style="text-align:center; padding: 2rem;">No sources cataloged.</td></tr>`}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading sources: ${e.message}</div>`;
        }
    },

    // 7. Complete 20-Report Center
    async renderReports() {
        const container = document.getElementById("view-admin-reports");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading 20-Report Catalog...</div>`;

        try {
            const res = await API.getReports();
            const reports = res.reports || [];
            const history = await API.getReportHistory(10);

            // Group reports by Groups A, B, C, D
            const groupA = reports.filter(r => ["01", "02", "03", "04"].includes(r.number));
            const groupB = reports.filter(r => ["05", "06", "07", "08"].includes(r.number));
            const groupC = reports.filter(r => ["09", "10", "11", "12", "13", "14", "15", "16"].includes(r.number));
            const groupD = reports.filter(r => ["17", "18", "19", "20"].includes(r.number));

            const renderGroupCards = (title, groupReports) => `
                <div style="margin-bottom: 2rem;">
                    <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 1rem; border-bottom: 2px solid var(--border-subtle); padding-bottom: 0.5rem;">${title}</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem;">
                        ${groupReports.map(r => `
                            <div class="card" style="margin-bottom: 0;">
                                <div class="card-header">
                                    <div>
                                        <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary);">Report ${r.number}: ${r.title}</h4>
                                        <div style="font-size: 0.75rem; color: var(--text-muted);">${r.category}</div>
                                    </div>
                                </div>
                                <div class="card-body">
                                    <p style="font-size: 0.8rem; color: var(--text-secondary); min-height: 40px; margin-bottom: 0.75rem;">${r.description}</p>
                                    ${r.last_generated ? `
                                        <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.75rem; background: var(--bg-surface); padding: 0.5rem; border-radius: 4px;">
                                            <div>Last Generated: <strong>${r.last_generated.generated_at ? r.last_generated.generated_at.slice(0, 19).replace('T', ' ') : 'N/A'}</strong></div>
                                            <div>Records: <strong>${r.last_generated.total_records || 0}</strong></div>
                                        </div>
                                    ` : ""}
                                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-subtle); padding-top: 0.75rem;">
                                        <button class="btn btn-primary btn-sm" onclick="generateReportPrompt('${r.number}')">Generate Now</button>
                                        ${r.last_generated && r.last_generated.file_paths ? `
                                            <div style="display: flex; gap: 4px;">
                                                ${Object.entries(r.last_generated.file_paths).map(([fmt, path]) => {
                                                    const fname = path.split(/[\/\\]/).pop();
                                                    return `<a href="/api/reports/download/${fname}" class="btn btn-outline btn-sm" style="font-size: 0.7rem; padding: 2px 6px;" download>${fmt.toUpperCase()}</a>`;
                                                }).join("")}
                                            </div>
                                        ` : ""}
                                    </div>
                                </div>
                            </div>
                        `).join("")}
                    </div>
                </div>
            `;

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">The Complete 20-Report Center</h1>
                        <p class="page-description">Generate, download, and configure publication-grade reports across PDF, Excel, CSV, and Interactive HTML</p>
                    </div>
                    <div class="header-actions">
                        <button class="btn btn-primary" onclick="generateAllReports()">Generate All 20 Reports</button>
                    </div>
                </div>

                ${renderGroupCards("Group A — Scholarships", groupA)}
                ${renderGroupCards("Group B — Internships", groupB)}
                ${renderGroupCards("Group C — Additional Academic & Career Opportunities", groupC)}
                ${renderGroupCards("Group D — Action, Matches & Intelligence", groupD)}

                <!-- Recent Generation History -->
                <div class="card" style="margin-top: 2rem;">
                    <div class="card-header">
                        <h3 class="card-title">Recent Report Generation History</h3>
                    </div>
                    <div class="card-body" style="padding: 0;">
                        <div class="table-responsive">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Report #</th>
                                        <th>Title</th>
                                        <th>Generated At</th>
                                        <th>Total Records</th>
                                        <th>Download Files</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${(history.history || []).map(h => `
                                        <tr>
                                            <td><strong>${h.report_number}</strong></td>
                                            <td>${h.report_title}</td>
                                            <td>${h.generated_at ? h.generated_at.slice(0, 19).replace('T', ' ') : '-'}</td>
                                            <td>${h.total_records}</td>
                                            <td>
                                                <div style="display: flex; gap: 4px;">
                                                    ${Object.entries(h.file_paths || {}).map(([fmt, path]) => {
                                                        const fname = path.split(/[\/\\]/).pop();
                                                        return `<a href="/api/reports/download/${fname}" class="btn btn-outline btn-sm" style="font-size: 0.72rem; padding: 2px 6px;" download>${fmt.toUpperCase()}</a>`;
                                                    }).join("")}
                                                </div>
                                            </td>
                                        </tr>
                                    `).join("") || `<tr><td colspan="5" style="text-align:center; padding: 2rem;">No historical reports generated yet.</td></tr>`}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading reports: ${e.message}</div>`;
        }
    },

    // 8. Schedules & Automation
    async renderSchedules() {
        const container = document.getElementById("view-admin-schedules");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading automation schedules...</div>`;

        try {
            const res = await API.getSchedules();
            const schedules = res.schedules || [];

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">Schedules & Automation Center</h1>
                        <p class="page-description">Automated background triggers for discovery, deadline monitoring, and weekly report compilation</p>
                    </div>
                </div>

                <div class="card">
                    <div class="card-body" style="padding: 0;">
                        <div class="table-responsive">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Schedule ID</th>
                                        <th>Workflow / Task</th>
                                        <th>Frequency</th>
                                        <th>Time Zone</th>
                                        <th>Status</th>
                                        <th>Next Run</th>
                                        <th>Last Run</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${schedules.map(s => `
                                        <tr>
                                            <td><code>${s.id}</code></td>
                                            <td><strong>${s.title}</strong></td>
                                            <td>${s.frequency}</td>
                                            <td>${s.timezone}</td>
                                            <td><span class="badge ${s.status === 'active' ? 'badge-open' : 'badge-closed'}">${s.status}</span></td>
                                            <td>${s.next_run}</td>
                                            <td>${s.last_run}</td>
                                            <td>
                                                <button class="btn btn-primary btn-sm" onclick="triggerScheduleRun('${s.id}')">Trigger Now</button>
                                            </td>
                                        </tr>
                                    `).join("")}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading schedules: ${e.message}</div>`;
        }
    },

    // 9. Students Directory
    async renderStudents() {
        const container = document.getElementById("view-admin-students");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading student directory...</div>`;

        try {
            const res = await API.getStudents();
            const students = res.students || [];

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">Student Directory & Academic Profiles</h1>
                        <p class="page-description">Authorized administrative overview of registered student profiles and academic criteria</p>
                    </div>
                </div>

                <div class="card">
                    <div class="card-body" style="padding: 0;">
                        <div class="table-responsive">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Student Name</th>
                                        <th>University</th>
                                        <th>Sector</th>
                                        <th>Degree & Discipline</th>
                                        <th>Semester</th>
                                        <th>CGPA</th>
                                        <th>Domicile</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${students.map(s => `
                                        <tr>
                                            <td>
                                                <strong>${s.full_name || s.name}</strong>
                                                <div style="font-size: 0.72rem; color: var(--text-muted);">${s.email}</div>
                                            </td>
                                            <td>${s.university}</td>
                                            <td>${UI.renderSectorBadge(s.university_type)}</td>
                                            <td>${s.degree_level} - ${s.discipline}</td>
                                            <td>Semester ${s.current_semester}</td>
                                            <td><strong>${s.cgpa}</strong></td>
                                            <td><span class="badge badge-charsadda">${s.domicile_district || 'KP'}</span></td>
                                            <td>
                                                <button class="btn btn-outline btn-sm" onclick="switchToStudentView('${s.id}')">Inspect Matches</button>
                                            </td>
                                        </tr>
                                    `).join("") || `<tr><td colspan="8" style="text-align:center; padding: 2rem;">No students registered yet.</td></tr>`}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading students: ${e.message}</div>`;
        }
    },

    // 10. System Settings
    async renderSettings() {
        const container = document.getElementById("view-admin-settings");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading system configuration...</div>`;

        try {
            const settings = await API.getSettings();

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">System Settings & Platform Configuration</h1>
                        <p class="page-description">Configure product identity, AI model parameters, notification credentials, and execution thresholds</p>
                    </div>
                    <div class="header-actions">
                        <button class="btn btn-primary" onclick="savePlatformSettings()">Save All Settings</button>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                    <!-- Platform Identity -->
                    <div class="card">
                        <div class="card-header"><h3 class="card-title">Product Identity & Brand</h3></div>
                        <div class="card-body">
                            <div class="form-group" style="margin-bottom: 1rem;">
                                <label class="form-label">Platform Name</label>
                                <input type="text" id="setting-platform-name" class="form-control" value="${settings.platform_name || 'Student Opportunity Intelligence'}">
                            </div>
                            <div class="form-group" style="margin-bottom: 1rem;">
                                <label class="form-label">Subtitle / Motto</label>
                                <input type="text" id="setting-subtitle" class="form-control" value="${settings.subtitle || 'Discover. Qualify. Apply. Achieve.'}">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Timezone</label>
                                <input type="text" class="form-control" value="Asia/Karachi (PKT, UTC+5)" disabled>
                            </div>
                        </div>
                    </div>

                    <!-- AI Provider Configuration -->
                    <div class="card">
                        <div class="card-header"><h3 class="card-title">AI Engine (Google Gemini)</h3></div>
                        <div class="card-body">
                            <div class="form-group" style="margin-bottom: 1rem;">
                                <label class="form-label">Configured Model</label>
                                <select id="setting-ai-model" class="form-select">
                                    <option value="gemini-2.5-flash" ${settings.ai_model === 'gemini-2.5-flash' ? 'selected' : ''}>gemini-2.5-flash (Fast & Cost Efficient)</option>
                                    <option value="gemini-1.5-flash" ${settings.ai_model === 'gemini-1.5-flash' ? 'selected' : ''}>gemini-1.5-flash</option>
                                    <option value="gemini-2.0-flash" ${settings.ai_model === 'gemini-2.0-flash' ? 'selected' : ''}>gemini-2.0-flash</option>
                                </select>
                            </div>
                            <div class="form-group" style="margin-bottom: 1rem;">
                                <label class="form-label">Daily Budget Limit (USD)</label>
                                <input type="number" id="setting-budget" class="form-control" value="${settings.max_daily_budget_usd || 5.0}" step="0.5">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Charsadda Priority Scoring Weight</label>
                                <input type="number" id="setting-charsadda-weight" class="form-control" value="${settings.charsadda_priority_weight || 1.2}" step="0.1">
                            </div>
                        </div>
                    </div>

                    <!-- Email & Notification Settings -->
                    <div class="card">
                        <div class="card-header"><h3 class="card-title">Notification & Email Dispatch</h3></div>
                        <div class="card-body">
                            <div class="form-group" style="margin-bottom: 1rem;">
                                <label class="form-label">Primary Owner Email (07:00 PKT)</label>
                                <input type="email" id="setting-owner-email" class="form-control" value="${settings.owner_email || ''}">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Resend Sender Email</label>
                                <input type="text" id="setting-resend-sender" class="form-control" value="${settings.resend_from_email || 'onboarding@resend.dev'}">
                            </div>
                        </div>
                    </div>

                    <!-- Automation Schedule -->
                    <div class="card">
                        <div class="card-header"><h3 class="card-title">Daily Pipeline Automation</h3></div>
                        <div class="card-body">
                            <div class="form-group" style="margin-bottom: 1rem;">
                                <label class="form-label">Pipeline Trigger Time (PKT)</label>
                                <input type="time" id="setting-schedule-time" class="form-control" value="${settings.schedule_time || '07:00'}">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Default Report Attachment Formats</label>
                                <div style="display: flex; gap: 1rem; margin-top: 0.5rem;">
                                    <label><input type="checkbox" checked disabled> PDF</label>
                                    <label><input type="checkbox" checked disabled> XLSX</label>
                                    <label><input type="checkbox" checked disabled> CSV</label>
                                    <label><input type="checkbox" checked disabled> HTML</label>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading settings: ${e.message}</div>`;
        }
    },

    // 11. System Health & Audit Logs
    async renderHealthAndAudit() {
        const container = document.getElementById("view-admin-health");
        container.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading health telemetry and audit logs...</div>`;

        try {
            const health = await API.getHealth();
            const auditLogs = await API.getAuditLogs(30);

            container.innerHTML = `
                <div class="page-header">
                    <div>
                        <h1 class="page-title">System Health & Administrative Audit Logs</h1>
                        <p class="page-description">Real-time infrastructure health and immutable administrative action trail</p>
                    </div>
                </div>

                <!-- Health Cards -->
                <div class="metric-grid">
                    ${UI.renderMetricCard("Server Status", health.status.toUpperCase(), "FastAPI REST API", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`)}
                    ${UI.renderMetricCard("Database Engine", "SQLite + JSON Sync", "WAL Mode Enabled", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>`)}
                    ${UI.renderMetricCard("AI Provider", "Google Gemini API", "Search Grounding Active", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10H12V2z"/></svg>`)}
                    ${UI.renderMetricCard("Report Storage", "Local reports/ directory", "PDF/XLSX/CSV/HTML", `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>`)}
                </div>

                <!-- Audit Logs Table -->
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Administrative Audit Trail</h3></div>
                    <div class="card-body" style="padding: 0;">
                        <div class="table-responsive">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Timestamp</th>
                                        <th>Actor</th>
                                        <th>Action</th>
                                        <th>Target Type</th>
                                        <th>Target ID</th>
                                        <th>Details</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${auditLogs.map(log => `
                                        <tr>
                                            <td>${log.created_at ? log.created_at.slice(0, 19).replace('T', ' ') : '-'}</td>
                                            <td><span class="badge badge-public">${log.actor}</span></td>
                                            <td><strong>${log.action}</strong></td>
                                            <td>${log.target_type || '-'}</td>
                                            <td><code>${log.target_id || '-'}</code></td>
                                            <td>${log.details || '-'}</td>
                                        </tr>
                                    `).join("") || `<tr><td colspan="6" style="text-align:center; padding: 2rem;">No administrative audit logs recorded yet.</td></tr>`}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color: var(--danger); padding: 2rem;">Error loading health & audit logs: ${e.message}</div>`;
        }
    }
};

window.ViewsAdmin = ViewsAdmin;
