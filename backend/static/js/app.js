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

// Quick Reflection / Emotion Analyzer
async function handleEmotion() {
  const inputEl = document.getElementById("emotion-input");
  const sendEl = document.getElementById("emotion-send");
  const text = inputEl ? inputEl.value.trim() : "";
  if (!text) return;

  if (sendEl) {
    sendEl.disabled = true;
    sendEl.textContent = "Analyzing...";
  }

  try {
    const data = await postJSON("/emotion", { text });
    
    // Display results in the DOM
    const container = document.getElementById("emotion-result-container");
    if (container) container.style.display = "block";

    const valLabel = document.getElementById("emotion-value-label");
    if (valLabel) {
      valLabel.textContent = `Emotion: ${data.emotion.emotion}`;
    }

    const priority = document.getElementById("triage-priority");
    if (priority) {
      priority.textContent = data.triage.urgency.toUpperCase();
      priority.className = `triage-priority-badge badge-${data.triage.urgency}`;
      
      // Update color coding based on urgency
      if (data.triage.urgency === "high") {
        priority.style.background = "rgba(244, 63, 94, 0.2)";
        priority.style.color = "var(--danger)";
      } else if (data.triage.urgency === "medium") {
        priority.style.background = "rgba(245, 158, 11, 0.2)";
        priority.style.color = "var(--warning)";
      } else {
        priority.style.background = "rgba(16, 185, 129, 0.2)";
        priority.style.color = "var(--success)";
      }
    }

    const message = document.getElementById("triage-message");
    if (message) {
      message.textContent = data.triage.message;
    }
  } catch (e) {
    console.error("Emotion analysis failed:", e);
  } finally {
    if (sendEl) {
      sendEl.disabled = false;
      sendEl.textContent = "🔍 Get Perspective";
    }
  }
}

// Password Update (Profile Page)
async function handlePasswordUpdate() {
  const oldPassword = document.getElementById("old-password").value;
  const newPassword = document.getElementById("new-password").value;
  const msg = document.getElementById("password-message");
  if (!oldPassword || !newPassword) return;
  
  try {
    const data = await postJSON("/account/password", {
      old_password: oldPassword,
      new_password: newPassword,
    });
    msg.textContent = data.message;
    msg.style.color = "var(--success)";
  } catch (e) {
    msg.textContent = "Password update failed.";
    msg.style.color = "var(--danger)";
  }
}

// Global Logout
async function logout() {
  const logoutBtnEl = document.getElementById("logout-btn");
  if (logoutBtnEl) {
    logoutBtnEl.disabled = true;
    logoutBtnEl.textContent = "Logging out...";
  }
  try {
    await postJSON("/logout", {});
    window.location.href = "/login";
  } catch (e) {
    console.error("Logout failed:", e);
    window.location.href = "/login";
  }
}

// Initialize Global Interactivity immediately
function initGlobalApp() {
  // 1. Theme Toggle
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

  // 2. Bind Profile Password Update
  const passwordSaveEl = document.getElementById("password-save");
  if (passwordSaveEl) {
    passwordSaveEl.addEventListener("click", handlePasswordUpdate);
  }

  // 3. Bind Logout Button
  const logoutBtnEl = document.getElementById("logout-btn");
  if (logoutBtnEl) {
    logoutBtnEl.addEventListener("click", logout);
  }

  // 4. Bind Quick Reflection Emotion Analyzer
  const emotionSendEl = document.getElementById("emotion-send");
  if (emotionSendEl) {
    emotionSendEl.addEventListener("click", handleEmotion);
  }
}

// Run setup immediately since script is loaded at the bottom of the body
initGlobalApp();

