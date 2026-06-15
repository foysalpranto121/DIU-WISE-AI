async function postJSON(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

function setMessage(message) {
  document.getElementById("auth-message").textContent = message;
}

async function login() {
  try {
    await postJSON("/login", {
      email: document.getElementById("login-email").value,
      password: document.getElementById("login-password").value,
    });
    window.location.href = "/";
  } catch (e) {
    setMessage(e.message);
  }
}

async function register() {
  try {
    await postJSON("/register", {
      full_name: document.getElementById("reg-name").value,
      email: document.getElementById("reg-email").value,
      password: document.getElementById("reg-password").value,
    });
    window.location.href = "/";
  } catch (e) {
    setMessage(e.message);
  }
}

document.getElementById("login-btn").addEventListener("click", login);
document.getElementById("register-btn").addEventListener("click", register);

// Theme Toggle
const themeToggleBtn = document.getElementById("theme-toggle-btn");
if (themeToggleBtn) {
  themeToggleBtn.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
  });
}
