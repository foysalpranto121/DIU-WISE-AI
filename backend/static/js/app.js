async function getJSON(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error("Request failed");
  return response.json();
}

async function postJSON(url, payload) {
  return getJSON(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

function renderStats(data) {
  const cards = document.getElementById("stats-cards");
  const high = data.burnout_summary.High || 0;
  const medium = data.burnout_summary.Medium || 0;
  cards.innerHTML = `
    <div class="card"><h4>Total Students</h4><div class="value">${data.total_students}</div></div>
    <div class="card"><h4>At Risk</h4><div class="value">${data.at_risk_students.length}</div></div>
    <div class="card"><h4>High Burnout</h4><div class="value">${high}</div></div>
    <div class="card"><h4>Medium Burnout</h4><div class="value">${medium}</div></div>
  `;
}

function renderTrends(trends) {
  const root = document.getElementById("trend-bars");
  const max = Math.max(...trends.map((t) => t.stress_index), 1);
  root.innerHTML = trends
    .map((t) => {
      const h = Math.round((t.stress_index / max) * 150);
      return `
        <div class="bar-col">
          <div class="bar" style="height:${h}px"></div>
          <div class="bar-label">${t.period}</div>
        </div>
      `;
    })
    .join("");
}

function renderHeatmap(items) {
  const root = document.getElementById("heatmap");
  root.innerHTML = items
    .map((h) => {
      const opacity = Math.min(h.stress / 10, 1);
      return `<div class="heat" style="opacity:${opacity}">${h.zone}: ${h.stress}</div>`;
    })
    .join("");
}

function renderRiskTable(rows) {
  const body = document.getElementById("risk-table-body");
  body.innerHTML = rows
    .map(
      (r) => `
      <tr>
        <td>${r.student_id}</td>
        <td>${r.burnout_risk}</td>
        <td>${r.distress_level}</td>
        <td>${r.stress_label}</td>
      </tr>
    `
    )
    .join("");
}

// Chat is now handled by chat.js — removed duplicate handler here.

async function handleEmotion() {
  const text = document.getElementById("emotion-input").value.trim();
  if (!text) return;
  const data = await postJSON("/emotion", { text });
  document.getElementById("emotion-result").textContent = JSON.stringify(data, null, 2);
}

async function handlePredict() {
  const payload = {
    attendance_rate: Number(document.getElementById("attendance").value || 0),
    submission_delay: Number(document.getElementById("delay").value || 0),
    grades: Number(document.getElementById("grades").value || 0),
    activity_score: Number(document.getElementById("activity").value || 0),
    engagement_decline: Number(document.getElementById("decline").value || 0),
  };
  const data = await postJSON("/predict", payload);
  document.getElementById("predict-result").textContent = JSON.stringify(data, null, 2);
}

async function handlePasswordUpdate() {
  const oldPassword = document.getElementById("old-password").value;
  const newPassword = document.getElementById("new-password").value;
  const msg = document.getElementById("password-message");
  try {
    const data = await postJSON("/account/password", {
      old_password: oldPassword,
      new_password: newPassword,
    });
    msg.textContent = data.message;
  } catch (e) {
    msg.textContent = "Password update failed.";
  }
}

async function loadMe() {
  const me = await getJSON("/me");
  if (!me.authenticated) {
    window.location.href = "/login";
    return;
  }
  const meLabel = document.getElementById("me-label");
  if (meLabel) meLabel.textContent = `${me.user.full_name} (${me.user.role})`;
  const adminLink = document.getElementById("admin-link");
  if (adminLink && me.user.role === "admin") {
    adminLink.classList.remove("hidden");
  }
}

async function logout() {
  await postJSON("/logout", {});
  window.location.href = "/login";
}

async function init() {
  try {
    await loadMe();
    const data = await getJSON("/dashboard-data");
    if (document.getElementById("stats-cards")) renderStats(data);
    if (document.getElementById("trend-bars")) renderTrends(data.wellness_trends);
    if (document.getElementById("heatmap")) renderHeatmap(data.stress_heatmap);
    if (document.getElementById("risk-table-body")) renderRiskTable(data.at_risk_students);
  } catch (e) {
    console.error(e);
  }

  // Bind only if elements exist (chat is handled by chat.js)
  const emotionSendEl = document.getElementById("emotion-send");
  if (emotionSendEl) emotionSendEl.addEventListener("click", handleEmotion);
  const predictSendEl = document.getElementById("predict-send");
  if (predictSendEl) predictSendEl.addEventListener("click", handlePredict);
  const passwordSaveEl = document.getElementById("password-save");
  if (passwordSaveEl) passwordSaveEl.addEventListener("click", handlePasswordUpdate);
  const logoutBtnEl = document.getElementById("logout-btn");
  if (logoutBtnEl) logoutBtnEl.addEventListener("click", logout);

  // Theme Toggle
  const themeToggleEl = document.getElementById("theme-toggle-btn");
  if (themeToggleEl) {
    themeToggleEl.addEventListener("click", () => {
      const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
      const newTheme = currentTheme === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", newTheme);
      localStorage.setItem("theme", newTheme);
      window.dispatchEvent(new CustomEvent("themechanged", { detail: { theme: newTheme } }));
    });
  }
}

init();
