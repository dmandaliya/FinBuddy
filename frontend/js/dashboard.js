// dashboard.js — loads all the data for the main dashboard page

requireAuth();
loadSidebarUser();

// We'll store the category chart instance here so we can destroy + redraw if needed
let categoryChart = null;

async function loadDashboard() {
  try {
    // Load accounts, transaction summary, and recent transactions in parallel
    const [accountsData, summaryData, recentData] = await Promise.all([
      apiGet("/plaid/accounts"),
      apiGet("/api/transactions/summary", { days: 30 }),
      apiGet("/api/transactions/recent", { limit: 8 }),
    ]);

    renderMetrics(accountsData, summaryData);
    renderCategoryChart(summaryData.by_category || {});
    renderBudgetBars(summaryData.by_category || {}, summaryData.budgets || {});
    renderRecentTx(recentData.transactions || []);

  } catch (err) {
    console.error("Dashboard load error:", err);
  }
}

function renderMetrics(accountsData, summaryData) {
  // Total available balance across all accounts
  const accounts = accountsData.accounts || [];
  const totalBalance = accounts.reduce((sum, a) => sum + (a.balance_available ?? a.balance_current ?? 0), 0);

  document.getElementById("metric-balance").textContent = fmt(totalBalance);
  document.getElementById("metric-spent").textContent = fmt(summaryData.total_spending || 0);

  const income = summaryData.total_income || 0;
  document.getElementById("metric-income").textContent = fmt(income);

  const net = summaryData.net || 0;
  const netEl = document.getElementById("metric-net");
  netEl.textContent = (net >= 0 ? "+" : "") + fmt(net);
  netEl.className = "metric-value " + (net >= 0 ? "positive" : "negative");

  // Personalized greeting using the user's name
  const name = localStorage.getItem("finbuddy_name") || "there";
  const greeting = document.getElementById("greeting");
  if (greeting) {
    const hour = new Date().getHours();
    const tod = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
    greeting.textContent = `${tod}, ${name}! Here's your financial snapshot.`;
  }
}

function renderCategoryChart(byCategory) {
  const canvas = document.getElementById("chart-category");
  if (!canvas) return;

  const labels = Object.keys(byCategory);
  const values = Object.values(byCategory);

  if (labels.length === 0) {
    canvas.parentElement.innerHTML += `<p class="text-muted" style="font-size:14px; margin-top:12px;">No spending data yet.</p>`;
    return;
  }

  // Destroy old chart if it exists (happens on refresh)
  if (categoryChart) categoryChart.destroy();

  const colors = ["#14b8a6","#f59e0b","#ef4444","#8b5cf6","#3b82f6","#22c55e","#f97316","#ec4899"];

  categoryChart = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors.slice(0, labels.length),
        borderColor: "#0f172a",
        borderWidth: 3,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#94a3b8", font: { size: 12 }, padding: 12 },
        },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.label}: $${ctx.parsed.toFixed(2)}`,
          },
        },
      },
    },
  });
}

function renderBudgetBars(byCategory, budgets) {
  const container = document.getElementById("budget-bars");
  if (!container) return;

  const entries = Object.entries(budgets);
  if (entries.length === 0) {
    container.innerHTML = `<div class="text-muted" style="font-size:14px; padding:20px 0;">No budgets set yet. <a href="budget.html">Set them up →</a></div>`;
    return;
  }

  container.innerHTML = entries.map(([cat, limit]) => {
    const spent = byCategory[cat] || 0;
    const pct = Math.min((spent / limit) * 100, 100);
    const fillClass = pct >= 100 ? "over" : pct >= 80 ? "warn" : "";
    return `
      <div class="budget-item">
        <div class="budget-header">
          <span class="budget-name" style="text-transform:capitalize;">${cat}</span>
          <span class="budget-amounts">${fmt(spent)} / ${fmt(limit)}</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill ${fillClass}" style="width:${pct}%"></div>
        </div>
      </div>
    `;
  }).join("");
}

function renderRecentTx(transactions) {
  const tbody = document.getElementById("recent-tx-body");
  if (!tbody) return;

  if (transactions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-muted" style="text-align:center; padding:28px;">
      No transactions yet. <a href="bank.html">Link a bank account →</a>
    </td></tr>`;
    return;
  }

  tbody.innerHTML = transactions.map(t => `
    <tr>
      <td class="text-muted" style="white-space:nowrap;">${t.date}</td>
      <td>${t.merchant_name || t.name}</td>
      <td>${categoryBadge(t.category)}</td>
      <td class="${t.amount > 0 ? "amount-out" : "amount-in"}" style="text-align:right;">
        ${t.amount > 0 ? "-" : "+"}${fmt(t.amount)}
      </td>
    </tr>
  `).join("");
}

// Kick everything off
loadDashboard();
