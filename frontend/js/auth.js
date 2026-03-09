// auth.js — handles login and signup on login.html

const API = window.API_BASE;

// If already logged in, go straight to dashboard
if (localStorage.getItem("finbuddy_token")) {
  window.location.href = "index.html";
}

function showTab(tab) {
  document.getElementById("login-form").classList.toggle("hidden", tab !== "login");
  document.getElementById("signup-form").classList.toggle("hidden", tab !== "signup");
  document.getElementById("tab-login").classList.toggle("active", tab === "login");
  document.getElementById("tab-signup").classList.toggle("active", tab === "signup");
  document.getElementById("alert-box").innerHTML = "";
}

function showAlert(msg, type = "error") {
  const icons = { success: "✅", error: "❌", warn: "⚠️", info: "ℹ️" };
  document.getElementById("alert-box").innerHTML = `
    <div class="alert alert-${type}">
      <span>${icons[type]}</span><span>${msg}</span>
    </div>
  `;
}

async function handleLogin(e) {
  e.preventDefault();
  const btn = document.getElementById("login-btn");
  btn.disabled = true;
  btn.textContent = "Signing in...";

  try {
    const res = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: document.getElementById("login-email").value.trim(),
        password: document.getElementById("login-password").value,
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Login failed");

    localStorage.setItem("finbuddy_token", data.access_token);
    localStorage.setItem("finbuddy_name", data.name);
    localStorage.setItem("finbuddy_user_id", data.user_id);
    window.location.href = "index.html";

  } catch (err) {
    showAlert(err.message);
    btn.disabled = false;
    btn.textContent = "Sign in";
  }
}

async function handleSignup(e) {
  e.preventDefault();
  const btn = document.getElementById("signup-btn");
  btn.disabled = true;
  btn.textContent = "Creating account...";

  try {
    const res = await fetch(`${API}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: document.getElementById("signup-name").value.trim(),
        email: document.getElementById("signup-email").value.trim(),
        password: document.getElementById("signup-password").value,
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Signup failed");

    localStorage.setItem("finbuddy_token", data.access_token);
    localStorage.setItem("finbuddy_name", data.name);
    localStorage.setItem("finbuddy_user_id", data.user_id);
    window.location.href = "index.html";

  } catch (err) {
    showAlert(err.message);
    btn.disabled = false;
    btn.textContent = "Create account";
  }
}
