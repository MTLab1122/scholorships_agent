/**
 * Reusable UI Component Renderers & Helpers
 * Student Opportunity Intelligence Platform
 */

const UI = {
    // 1. Metric KPI Card
    renderMetricCard(title, value, sub, iconSvg, trend = "") {
        return `
            <div class="metric-card">
                <div class="metric-info">
                    <span class="metric-label">${title}</span>
                    <span class="metric-value">${value}</span>
                    ${sub ? `<span class="metric-sub">${sub}</span>` : ""}
                </div>
                <div class="metric-icon-box">
                    ${iconSvg}
                </div>
            </div>
        `;
    },

    // 2. Status Badge
    renderStatusBadge(status, daysLeft) {
        let badgeClass = "badge-closed";
        let label = status || "Unknown";

        if (status === "Open") {
            badgeClass = "badge-open";
            label = daysLeft !== null && daysLeft !== undefined 
                ? `Open (${daysLeft}d left)` 
                : "Open";
        } else if (status === "Closing soon") {
            badgeClass = "badge-closing";
            label = daysLeft !== null && daysLeft !== undefined 
                ? `Closing Soon (${daysLeft}d left)` 
                : "Closing Soon";
        } else if (status === "Closed" || status === "Expired") {
            badgeClass = "badge-closed";
        }

        return `<span class="badge ${badgeClass}">${label}</span>`;
    },

    // 3. Verification Badge
    renderVerificationBadge(badge, tier = 1) {
        if (badge === "Confirmed" || tier === 1) {
            return `<span class="badge badge-confirmed">Confirmed (Official Tier ${tier})</span>`;
        } else if (badge === "Via Partner") {
            return `<span class="badge badge-public">Via Partner</span>`;
        }
        return `<span class="badge badge-unverified">Unverified</span>`;
    },

    // 4. Sector Badge (Public vs Private)
    renderSectorBadge(sector) {
        const s = (sector || "").toLowerCase();
        if (s.includes("public")) {
            return `<span class="badge badge-public">Public Sector</span>`;
        } else if (s.includes("private")) {
            return `<span class="badge badge-private">Private Sector</span>`;
        } else if (s.includes("both")) {
            return `<span class="badge badge-public">Public & Private</span>`;
        }
        return `<span class="badge badge-closed">Sector: ${sector || "Not stated"}</span>`;
    },

    // 5. Regional Priority Badges (Charsadda & KP)
    renderPriorityBadges(opp) {
        let badges = [];
        if (opp.charsadda_flag) {
            badges.push(`<span class="badge badge-charsadda">★ Charsadda Priority</span>`);
        }
        if (opp.kp_flag) {
            badges.push(`<span class="badge badge-kp">KP Domicile</span>`);
        }
        if (opp.target_uni_flag) {
            badges.push(`<span class="badge badge-public">Target Uni</span>`);
        }
        return badges.join(" ");
    },

    // 6. Opportunity Card (Student View)
    renderOpportunityCard(opp, options = {}) {
        const isSaved = State.savedOpportunityIds.has(opp.id);
        const matchScore = options.matchScore !== undefined ? options.matchScore : null;
        const reasons = options.reasons || [];
        const unmet = options.unmet_criteria || [];

        return `
            <div class="opp-card" id="opp-card-${opp.id}">
                <div class="opp-card-header">
                    <div>
                        <div class="opp-title">${opp.name}</div>
                        <div class="opp-sponsor">${opp.sponsor} • <span style="text-transform: capitalize;">${opp.category || "Opportunity"}</span></div>
                    </div>
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        ${matchScore !== null ? `<span class="badge" style="background: rgba(2, 132, 199, 0.15); color: #0284C7; font-size: 0.85rem; font-weight: 700; padding: 4px 10px;">${matchScore}% Match</span>` : ""}
                        <button class="btn btn-outline btn-sm btn-icon-only" onclick="toggleSaveOpportunity('${opp.id}')" title="${isSaved ? 'Remove Bookmark' : 'Save Opportunity'}">
                            ${isSaved 
                                ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="#EAB308" stroke="#EAB308" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>`
                                : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>`}
                        </button>
                    </div>
                </div>

                <div class="opp-meta-row">
                    ${this.renderStatusBadge(opp.status, opp.days_left)}
                    ${this.renderVerificationBadge(opp.verification_badge, opp.source_trust_tier)}
                    ${this.renderSectorBadge(opp.university_types)}
                    ${this.renderPriorityBadges(opp)}
                    ${opp.deadline && opp.deadline !== 'not stated' ? `<span style="font-size: 0.75rem; color: var(--text-muted);">Deadline: <strong>${opp.deadline}</strong></span>` : ""}
                </div>

                ${opp.benefits && opp.benefits !== 'not stated' ? `
                    <div style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.4;">
                        <strong>Funding & Benefits:</strong> ${opp.benefits}
                    </div>
                ` : ""}

                ${reasons.length > 0 ? `
                    <div class="opp-reasons-box">
                        <strong>Match Justifications:</strong>
                        <ul>
                            ${reasons.map(r => `<li>${r}</li>`).join("")}
                        </ul>
                    </div>
                ` : ""}

                ${unmet.length > 0 ? `
                    <div style="background: rgba(239, 68, 68, 0.1); border-left: 3px solid #EF4444; border-radius: 4px; padding: 0.5rem 0.75rem; font-size: 0.78rem; color: #DC2626;">
                        <strong>Notice:</strong> ${unmet.join("; ")}
                    </div>
                ` : ""}

                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem; pt: 0.5rem; border-top: 1px solid var(--border-subtle); padding-top: 0.75rem;">
                    <div style="display: flex; gap: 0.75rem;">
                        ${opp.apply_url && opp.apply_url !== 'not stated' ? `<a href="${opp.apply_url}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm">Official Portal &rarr;</a>` : ""}
                        <button class="btn btn-outline btn-sm" onclick="openOpportunityDetail('${opp.id}')">View Full Details</button>
                    </div>
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="btn btn-secondary btn-sm" onclick="openPrepWorkspace('${opp.id}')">Prep Studio</button>
                        <button class="btn btn-primary btn-sm" onclick="trackOpportunity('${opp.id}')">+ Add to Applications</button>
                    </div>
                </div>
            </div>
        `;
    },

    // 7. Modal Helper
    showModal(title, bodyHtml, footerHtml = "") {
        let modal = document.getElementById("global-modal");
        if (!modal) {
            modal = document.createElement("div");
            modal.id = "global-modal";
            modal.className = "modal-backdrop";
            modal.innerHTML = `
                <div class="modal-box">
                    <div class="modal-header">
                        <h3 class="card-title" id="modal-title"></h3>
                        <button class="btn btn-outline btn-sm btn-icon-only" onclick="UI.closeModal()">&times;</button>
                    </div>
                    <div class="modal-body" id="modal-body"></div>
                    <div class="modal-footer" id="modal-footer"></div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        document.getElementById("modal-title").innerHTML = title;
        document.getElementById("modal-body").innerHTML = bodyHtml;
        const footer = document.getElementById("modal-footer");
        if (footerHtml) {
            footer.innerHTML = footerHtml;
            footer.style.display = "flex";
        } else {
            footer.style.display = "none";
        }

        modal.classList.add("active");
    },

    closeModal() {
        const modal = document.getElementById("global-modal");
        if (modal) modal.classList.remove("active");
    },

    // 8. Drawer Helper
    openDrawer(title, bodyHtml, footerHtml = "") {
        let drawer = document.getElementById("global-drawer");
        if (!drawer) {
            drawer = document.createElement("div");
            drawer.id = "global-drawer";
            drawer.className = "drawer-backdrop";
            drawer.innerHTML = `
                <div class="drawer-panel" id="drawer-panel">
                    <div class="modal-header">
                        <h3 class="card-title" id="drawer-title"></h3>
                        <button class="btn btn-outline btn-sm btn-icon-only" onclick="UI.closeDrawer()">&times;</button>
                    </div>
                    <div class="modal-body" id="drawer-body"></div>
                    <div class="modal-footer" id="drawer-footer"></div>
                </div>
            `;
            drawer.onclick = (e) => {
                if (e.target === drawer) UI.closeDrawer();
            };
            document.body.appendChild(drawer);
        }

        document.getElementById("drawer-title").innerHTML = title;
        document.getElementById("drawer-body").innerHTML = bodyHtml;
        const footer = document.getElementById("drawer-footer");
        if (footerHtml) {
            footer.innerHTML = footerHtml;
            footer.style.display = "flex";
        } else {
            footer.style.display = "none";
        }

        drawer.classList.add("active");
        setTimeout(() => {
            document.getElementById("drawer-panel").classList.add("active");
        }, 10);
    },

    closeDrawer() {
        const panel = document.getElementById("drawer-panel");
        const drawer = document.getElementById("global-drawer");
        if (panel) panel.classList.remove("active");
        setTimeout(() => {
            if (drawer) drawer.classList.remove("active");
        }, 200);
    },

    // 9. Toast Helper
    showToast(message, type = "info") {
        let container = document.getElementById("toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "toast-container";
            container.className = "toast-container";
            document.body.appendChild(container);
        }

        const toast = document.createElement("div");
        toast.className = "toast";
        
        let icon = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
        if (type === "success") {
            icon = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`;
        } else if (type === "error") {
            icon = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`;
        } else if (type === "warning") {
            icon = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
        }

        toast.innerHTML = `
            ${icon}
            <span style="flex:1;">${message}</span>
        `;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateX(100%)";
            toast.style.transition = "all 0.25s";
            setTimeout(() => toast.remove(), 250);
        }, 4000);
    },

    // 10. Empty State
    renderEmptyState(title, subtitle, actionHtml = "") {
        return `
            <div class="empty-state">
                <div class="empty-state-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                </div>
                <div class="empty-state-title">${title}</div>
                <div class="empty-state-desc">${subtitle}</div>
                ${actionHtml ? `<div>${actionHtml}</div>` : ""}
            </div>
        `;
    }
};

window.UI = UI;
