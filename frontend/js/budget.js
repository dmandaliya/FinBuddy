// budget.js — manages budgets, bills, and income sources

requireAuth();
loadSidebarUser();

async function loadAll() {
  await Promise.all([loadBudgets(), loadBills(), loadIncomeSources()]);
}

// ---- Budgets ----

async function loadBudgets() {
  const container = document.getElementById("budgets-list");
  try {
    const data = await apiGet("/api/budgets");
    const budgets = data.budgets || [];
    if (budgets.length === 0) {
      container.innerHTML = `<div class="text-muted" style="font-size:14px;">No budgets yet. Add one above.</div>`;
      return;
    }
    container.innerHTML = budgets.map(b => `
      <div class="flex-between" style="padding: 10px 0; border-bottom: 1px solid var(--border);">
        <div>
          <span style="font-weight:500; text-transform:capitalize;">${b.category}</span>
          <span class="text-muted" style="font-size:13px; margin-left:8px;">${fmt(b.monthly_limit)}/month</span>
        </div>
        <button class="btn btn-danger" style="padding:4px 10px; font-size:12px;" onclick="deleteBudget(${b.id})">Remove</button>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<div class="text-red" style="font-size:13px;">${err.message}</div>`;
  }
}

async function addBudget() {
  const cat = document.getElementById("new-budget-cat").value;
  const amount = parseFloat(document.getElementById("new-budget-amount").value);
  if (!cat || !amount || amount <= 0) {
    showAlert("Pick a category and enter a valid amount.", "warn");
    return;
  }
  try {
    await apiPost("/api/budgets", { category: cat, monthly_limit: amount });
    document.getElementById("new-budget-amount").value = "";
    showAlert(`Budget for ${cat} set to ${fmt(amount)}/month`, "success");
    loadBudgets();
  } catch (err) {
    showAlert(err.message, "error");
  }
}

async function deleteBudget(id) {
  try {
    await apiDelete(`/api/budgets/${id}`);
    loadBudgets();
  } catch (err) {
    showAlert(err.message, "error");
  }
}

// ---- Bills ----

async function loadBills() {
  const container = document.getElementById("bills-list");
  try {
    const data = await apiGet("/api/bills");
    const bills = data.bills || [];
    if (bills.length === 0) {
      container.innerHTML = `<div class="text-muted" style="font-size:14px;">No bills added yet.</div>`;
      return;
    }
    container.innerHTML = bills.map(b => `
      <div class="flex-between" style="padding: 10px 0; border-bottom: 1px solid var(--border);">
        <div>
          <span style="font-weight:500;">${b.name}</span>
          <span class="text-muted" style="font-size:13px; margin-left:8px;">${fmt(b.amount)} — due day ${b.due_day}</span>
        </div>
        <button class="btn btn-danger" style="padding:4px 10px; font-size:12px;" onclick="deleteBill(${b.id})">Remove</button>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<div class="text-red" style="font-size:13px;">${err.message}</div>`;
  }
}

async function addBill() {
  const name = document.getElementById("new-bill-name").value.trim();
  const amount = parseFloat(document.getElementById("new-bill-amount").value);
  const due_day = parseInt(document.getElementById("new-bill-day").value);

  if (!name || !amount || !due_day) {
    showAlert("Fill in all bill fields.", "warn");
    return;
  }
  try {
    await apiPost("/api/bills", { name, amount, due_day });
    document.getElementById("new-bill-name").value = "";
    document.getElementById("new-bill-amount").value = "";
    document.getElementById("new-bill-day").value = "";
    showAlert(`${name} bill added.`, "success");
    loadBills();
  } catch (err) {
    showAlert(err.message, "error");
  }
}

async function deleteBill(id) {
  try {
    await apiDelete(`/api/bills/${id}`);
    loadBills();
  } catch (err) {
    showAlert(err.message, "error");
  }
}

// ---- Income sources ----

async function loadIncomeSources() {
  const container = document.getElementById("income-list");
  try {
    const data = await apiGet("/api/income-sources");
    const sources = data.income_sources || [];
    if (sources.length === 0) {
      container.innerHTML = `<div class="text-muted" style="font-size:14px;">No income sources yet.</div>`;
      return;
    }
    container.innerHTML = sources.map(s => `
      <div class="flex-between" style="padding: 10px 0; border-bottom: 1px solid var(--border);">
        <div>
          <span style="font-weight:500;">${s.name}</span>
          <span class="text-muted" style="font-size:13px; margin-left:8px;">$${s.hourly_rate.toFixed(2)}/hr</span>
        </div>
        <button class="btn btn-danger" style="padding:4px 10px; font-size:12px;" onclick="deleteIncomeSource(${s.id})">Remove</button>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<div class="text-red" style="font-size:13px;">${err.message}</div>`;
  }
}

async function addIncomeSource() {
  const name = document.getElementById("new-income-name").value.trim();
  const hourly_rate = parseFloat(document.getElementById("new-income-rate").value);
  if (!name || !hourly_rate || hourly_rate <= 0) {
    showAlert("Enter a name and valid hourly rate.", "warn");
    return;
  }
  try {
    await apiPost("/api/income-sources", { name, hourly_rate });
    document.getElementById("new-income-name").value = "";
    document.getElementById("new-income-rate").value = "";
    showAlert(`${name} added at $${hourly_rate}/hr`, "success");
    loadIncomeSources();
  } catch (err) {
    showAlert(err.message, "error");
  }
}

async function deleteIncomeSource(id) {
  try {
    await apiDelete(`/api/income-sources/${id}`);
    loadIncomeSources();
  } catch (err) {
    showAlert(err.message, "error");
  }
}

// Need fmt for display — inline since api.js loads first
function fmt(amount) {
  return "$" + Math.abs(amount).toLocaleString("en-CA", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

loadAll();
