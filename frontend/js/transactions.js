// transactions.js — loads and displays the full transaction list with filters

requireAuth();
loadSidebarUser();

async function loadTransactions() {
  const days = document.getElementById("filter-days").value;
  const category = document.getElementById("filter-category").value;

  const tbody = document.getElementById("tx-body");
  tbody.innerHTML = `<tr><td colspan="4" class="text-muted" style="text-align:center; padding:28px;">Loading...</td></tr>`;

  try {
    const params = { days };
    if (category) params.category = category;

    const data = await apiGet("/api/transactions", params);
    const txs = data.transactions || [];

    document.getElementById("tx-count").textContent = txs.length;

    // Show the total spending for the filtered view
    const totalSpent = txs.filter(t => t.amount > 0).reduce((s, t) => s + t.amount, 0);
    document.getElementById("tx-total").textContent = `Total spending: ${fmt(totalSpent)}`;

    if (txs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-muted" style="text-align:center; padding:28px;">
        No transactions found. <a href="bank.html">Link a bank account →</a>
      </td></tr>`;
      return;
    }

    tbody.innerHTML = txs.map(t => `
      <tr>
        <td class="text-muted" style="white-space:nowrap;">${t.date}</td>
        <td>
          <div style="font-weight:500;">${t.merchant_name || t.name}</div>
          ${t.merchant_name && t.name !== t.merchant_name
            ? `<div class="text-muted" style="font-size:12px;">${t.name}</div>`
            : ""}
        </td>
        <td>${categoryBadge(t.category)}</td>
        <td class="${t.amount > 0 ? "amount-out" : "amount-in"}" style="text-align:right; white-space:nowrap;">
          ${t.amount > 0 ? "-" : "+"}${fmt(t.amount)}
          ${t.is_pending ? '<span class="text-muted" style="font-size:11px;"> (pending)</span>' : ""}
        </td>
      </tr>
    `).join("");

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:28px; color:var(--red);">
      Error: ${err.message}
    </td></tr>`;
  }
}

loadTransactions();
