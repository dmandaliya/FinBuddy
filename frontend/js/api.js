// api.js — shared helpers used by every page
// Handles auth token storage, fetch wrappers, and logout.

const API = window.API_BASE;

function getToken() {
  return localStorage.getItem("finbuddy_token");
}

function saveAuth(token, userId, name) {
  localStorage.setItem("finbuddy_token", token);
  localStorage.setItem("finbuddy_user_id", userId);
  localStorage.setItem("finbuddy_name", name);
}

function logout() {
  localStorage.clear();
  window.location.href = "login.html";
}

// Redirect to login if no token found — called at the top of every protected page
function requireAuth() {
  if (!getToken()) {
    window.location.href = "login.html";
  }
}

// Populate the sidebar name/email fields
function loadSidebarUser() {
  const name = localStorage.getItem("finbuddy_name") || "";
  const el = document.getElementById("sidebar-name");
  if (el) el.textContent = name;
}

// Authenticated GET
async function apiGet(path, params = {}) {
  const url = new URL(API + path);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));

  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });

  if (res.status === 401) { logout(); return; }

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

// Authenticated POST
async function apiPost(path, body = {}) {
  const res = await fetch(API + path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
    },
    body: JSON.stringify(body),
  });

  if (res.status === 401) { logout(); return; }

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

// Authenticated DELETE
async function apiDelete(path) {
  const res = await fetch(API + path, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  if (res.status === 401) { logout(); return; }
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

// Show an alert message inside an element with id="alert-box"
function showAlert(message, type = "info") {
  const box = document.getElementById("alert-box");
  if (!box) return;
  const icons = { success: "✅", error: "❌", warn: "⚠️", info: "ℹ️" };
  box.innerHTML = `
    <div class="alert alert-${type}">
      <span>${icons[type] || ""}</span>
      <span>${message}</span>
    </div>
  `;
  // Auto-clear after 6 seconds
  setTimeout(() => { box.innerHTML = ""; }, 6000);
}

// Format dollar amounts nicely: $1,234.56
function fmt(amount) {
  return "$" + Math.abs(amount).toLocaleString("en-CA", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// Map category slug to a CSS badge class
function categoryBadge(cat) {
  const map = {
    food: "badge-food", groceries: "badge-groceries", transport: "badge-transport",
    shopping: "badge-shopping", entertainment: "badge-entertainment",
    housing: "badge-housing", healthcare: "badge-healthcare",
    income: "badge-income", other: "badge-other",
  };
  const cls = map[cat] || "badge-other";
  const labels = {
    food: "Food", groceries: "Groceries", transport: "Transport",
    shopping: "Shopping", entertainment: "Entertainment",
    housing: "Housing", healthcare: "Healthcare",
    income: "Income", other: "Other",
  };
  return `<span class="badge ${cls}">${labels[cat] || cat}</span>`;
}
