const API = "";
const TOKEN_KEY = "anomai_token";
const USER_KEY = "anomai_user";

const $ = id => document.getElementById(id);
const token = () => localStorage.getItem(TOKEN_KEY);
const user = () => JSON.parse(localStorage.getItem(USER_KEY) || "null");

function showMessage(id, message, type = "success") {
    const el = $(id); el.textContent = message; el.className = `message ${type}`;
}
function hideMessage(id) { $(id).className = "message hidden"; }
function escapeHtml(v) { return String(v ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;"); }

async function api(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    if (token()) headers.Authorization = `Bearer ${token()}`;
    const response = await fetch(`${API}${path}`, { ...options, headers });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || data.error || "Request failed.");
    return data;
}

function renderNav() {
    const nav = $("navActions");
    if (!user()) { nav.innerHTML = ""; return; }
    nav.innerHTML = `<span>${escapeHtml(user().name)}</span><button class="nav-btn" id="historyBtn">History</button><button class="nav-btn" id="logoutBtn">Logout</button>`;
    $("historyBtn").onclick = () => location.href = `/anomai/${user().id}/history`;
    $("logoutBtn").onclick = () => { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); location.href = "/anomai"; };
}

function showWorkspace() { $("authView").classList.add("hidden"); $("historyView").classList.add("hidden"); $("appView").classList.remove("hidden"); renderNav(); }
function showAuth() { $("authView").classList.remove("hidden"); $("appView").classList.add("hidden"); $("historyView").classList.add("hidden"); renderNav(); }

$("loginTab").onclick = () => { $("loginTab").classList.add("active"); $("registerTab").classList.remove("active"); $("loginForm").classList.remove("hidden"); $("registerForm").classList.add("hidden"); };
$("registerTab").onclick = () => { $("registerTab").classList.add("active"); $("loginTab").classList.remove("active"); $("registerForm").classList.remove("hidden"); $("loginForm").classList.add("hidden"); };

$("loginForm").onsubmit = async e => {
    e.preventDefault(); hideMessage("authMessage");
    try {
        const data = await api("/api/auth/login", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({email:$("loginEmail").value,password:$("loginPassword").value}) });
        localStorage.setItem(TOKEN_KEY, data.token); localStorage.setItem(USER_KEY, JSON.stringify(data.user)); showWorkspace();
    } catch (error) { showMessage("authMessage", error.message, "error"); }
};

$("registerForm").onsubmit = async e => {
    e.preventDefault(); hideMessage("authMessage");
    try {
        const data = await api("/api/auth/register", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({name:$("registerName").value,email:$("registerEmail").value,password:$("registerPassword").value}) });
        localStorage.setItem(TOKEN_KEY, data.token); localStorage.setItem(USER_KEY, JSON.stringify(data.user)); showWorkspace();
    } catch (error) { showMessage("authMessage", error.message, "error"); }
};

$("dataset").onchange = () => { $("fileName").textContent = $("dataset").files[0]?.name || "Choose a dataset"; };

$("uploadForm").onsubmit = async e => {
    e.preventDefault();
    if (!$("dataset").files.length) return showMessage("uploadMessage", "Please select a dataset first.", "error");
    const form = new FormData(); form.append("dataset", $("dataset").files[0]);
    $("analyzeButton").disabled = true; $("analyzeButton").textContent = "Analyzing…";
    showMessage("uploadMessage", "Schema profiling, anomaly detection and remidiation are running…");
    try { const data = await api("/api/upload", { method:"POST", body:form }); renderDashboard(data); showMessage("uploadMessage", "Analysis completed successfully."); }
    catch(error) { showMessage("uploadMessage", error.message, "error"); }
    finally { $("analyzeButton").disabled = false; $("analyzeButton").textContent = "Analyze Dataset"; }
};

function renderDashboard(data) {
    $("dashboard").classList.remove("hidden");
    $("originalRows").textContent = data.dataset?.original_rows ?? "—";
    $("cleanedRows").textContent = data.dataset?.cleaned_rows ?? "—";
    $("columns").textContent = data.dataset?.cleaned_columns ?? "—";
    $("changesApplied").textContent = data.dataset?.changes_applied ?? "—";
    $("overallScore").textContent = `${Number(data.quality?.after?.overall_score ?? data.quality?.before?.overall_score ?? 0).toFixed(1)}`;
    $("mlScore").textContent = data.quality?.after?.ml_readiness_score != null ? `${Number(data.quality.after.ml_readiness_score).toFixed(1)}` : "—";
    $("interpretation").textContent = data.quality?.after?.interpretation || data.quality?.before?.interpretation || "";

    const schema = data.schema?.columns || data.profile?.columns || [];
    $("schemaRows").textContent = `${schema.length} columns`;
    $("schemaBody").innerHTML = schema.map(c => `<tr><td>${escapeHtml(c.name)}</td><td>${escapeHtml(c.data_type)}</td><td>${escapeHtml(c.semantic_role || "generic")}</td><td>${c.nullable ? "Yes" : "No"}</td></tr>`).join("");

    const q = data.quality?.after || data.quality?.before || {};
    $("qualityBox").innerHTML = [["Completeness",q.completeness],["Validity",q.validity],["Uniqueness",q.uniqueness],["Anomaly",q.anomaly_score]].map(([n,v]) => `<div class="quality-item"><span>${n}</span><strong>${Number(v ?? 0).toFixed(1)}</strong></div>`).join("");

    const s = data.anomalies?.before?.summary || {};
    $("detectionSummary").innerHTML = [["Evidence",s.total_evidence],["Findings",s.unique_findings],["Affected rows",s.affected_rows],["ML evidence",s.ml_evidence]].map(([n,v]) => `<div class="summary-box"><strong>${v ?? 0}</strong><span>${n}</span></div>`).join("");

    const findings = data.anomalies?.before?.findings || [];
    $("findingsBody").innerHTML = findings.length ? findings.map(f => `<tr><td>${f.source_row ?? "—"}</td><td>${escapeHtml(f.column || (f.affected_columns || []).map(x=>x.column).join(", ") || "Row-level")}</td><td>${escapeHtml((f.issue_types || [f.issue_type]).join(", ").replaceAll("_"," "))}</td><td>${escapeHtml((f.detection_methods || []).join(", "))}</td><td class="severity ${escapeHtml(f.severity)}">${escapeHtml(f.severity)}</td><td>${f.confidence != null ? `${Math.round(Number(f.confidence)*100)}%` : "—"}</td></tr>`).join("") : `<tr><td colspan="6">No anomalies detected.</td></tr>`;

    const changes = data.remidiation?.changes || [];
    const suggestions = data.remidiation?.suggestions || [];
    $("remidiationCount").textContent = `${changes.length} automatic · ${suggestions.length} review items`;
    $("remidiationBox").innerHTML = [...changes.map(c => `<div class="audit-item"><strong>✓ ${escapeHtml(c.action)}</strong><small>Row ${escapeHtml(c.source_row)} · ${escapeHtml(c.column || "row")}</small><div>${escapeHtml(c.reason)}</div><div>${escapeHtml(c.old_value)} → ${escapeHtml(c.new_value)}</div></div>`), ...suggestions.map(s => `<div class="audit-item"><strong>Review required</strong><small>Row ${escapeHtml((s.row_index ?? 0)+2)} · ${escapeHtml(s.column || "dataset")}</small><div>${escapeHtml(s.reason)}</div></div>`)].join("") || "<p>No remidiation changes or review items were generated.</p>";

    const download = data.cleaned_file;
    if (download) $("downloadButton").onclick = () => downloadFile(download.download_url, download.filename);
    $("downloadInfo").textContent = download ? `Cleaned ${download.format.toUpperCase()} file is ready. Analysis ID: ${data.history?.id || "—"}` : "No downloadable file was produced.";
}

async function downloadFile(url, filename) {
    try {
        const response = await fetch(url, { headers:{ Authorization:`Bearer ${token()}` } });
        if (!response.ok) { const d = await response.json().catch(()=>({})); throw new Error(d.error || "Download failed."); }
        const blob = await response.blob(); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = filename || "anomai_cleaned"; link.click(); URL.revokeObjectURL(link.href);
    } catch(error) { showMessage("uploadMessage", error.message, "error"); }
}

async function loadHistory() {
    const me = user();
    if (!me || !token()) return showAuth();
    $("authView").classList.add("hidden"); $("appView").classList.add("hidden"); $("historyView").classList.remove("hidden"); renderNav();
    try {
        const data = await api(`/api/users/${encodeURIComponent(me.id)}/history`);
        $("historyList").innerHTML = data.history.length ? data.history.map(h => `<div class="history-item"><div><strong>${escapeHtml(h.originalFilename)}</strong><small>${new Date(h.createdAt).toLocaleString()} · ${escapeHtml(h.format)} · ${h.dataset?.changesApplied ?? 0} changes · reliability ${Number(h.quality?.after?.overall_score ?? 0).toFixed(1)}</small></div><button class="secondary" data-history="${h._id}">View</button></div>`).join("") : "<p>No analyses yet. Return to the workspace and analyze your first dataset.</p>";
        document.querySelectorAll("[data-history]").forEach(btn => btn.onclick = () => loadHistoryItem(btn.dataset.history));
    } catch(error) { $("historyList").innerHTML = `<p class="error-text">${escapeHtml(error.message)}</p>`; }
}

async function loadHistoryItem(id) {
    try {
        const data = await api(`/api/users/${user().id}/history/${id}`);
        const h = data.history;
        $("historyList").innerHTML = `<button class="secondary" id="historyBack">← Back to history</button><div class="card" style="margin-top:15px"><h2>${escapeHtml(h.originalFilename)}</h2><p>Analyzed ${new Date(h.createdAt).toLocaleString()}</p><pre style="white-space:pre-wrap;overflow:auto">${escapeHtml(JSON.stringify({dataset:h.dataset,quality:h.quality,anomalies:h.anomalies?.before?.summary,remidiation:h.remidiation},null,2))}</pre></div>`;
        $("historyBack").onclick = loadHistory;
    } catch(error) { alert(error.message); }
}

$("backToApp").onclick = () => { location.href = "/anomai"; };

(async function init() {
    if (!token() || !user()) return showAuth();
    const path = location.pathname;
    if (/\/anomai\/[^/]+\/history$/.test(path)) return loadHistory();
    try { await api("/api/auth/me"); showWorkspace(); } catch (_error) { localStorage.clear(); showAuth(); }
})();
