// bank.js — handles bank linking (sandbox + real Plaid) and account display

requireAuth();
loadSidebarUser();
loadAccounts();

async function loadAccounts() {
  const container = document.getElementById("accounts-list");
  try {
    const data = await apiGet("/plaid/accounts");
    const accounts = data.accounts || [];

    if (accounts.length === 0) {
      container.innerHTML = `<div class="text-muted" style="font-size:14px; padding:20px 0;">No accounts connected yet.</div>`;
      return;
    }

    container.innerHTML = accounts.map(a => `
      <div class="card" style="margin-bottom:12px; padding:16px;">
        <div class="flex-between">
          <div>
            <div style="font-weight:600;">${a.official_name || a.name}</div>
            <div class="text-muted" style="font-size:12px; margin-top:2px;">
              ${a.type} · ${a.subtype} · ••••${a.mask || "????"}
            </div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:20px; font-weight:700; color:var(--accent);">
              $${(a.balance_available ?? a.balance_current ?? 0).toLocaleString("en-CA", {minimumFractionDigits:2})}
            </div>
            <div class="text-muted" style="font-size:11px;">available</div>
          </div>
        </div>
        ${a.last_synced
          ? `<div class="text-muted" style="font-size:11px; margin-top:8px;">Last synced: ${new Date(a.last_synced).toLocaleString()}</div>`
          : ""}
      </div>
    `).join("");

  } catch (err) {
    container.innerHTML = `<div class="text-red" style="font-size:14px;">Error loading accounts: ${err.message}</div>`;
  }
}

async function sandboxConnect() {
  const btn = document.getElementById("sandbox-btn");
  btn.disabled = true;
  btn.textContent = "Connecting...";
  try {
    const data = await apiPost("/plaid/sandbox_connect");
    showAlert(`Connected! Synced ${data.etl.transactions.inserted} transactions.`, "success");
    loadAccounts();
  } catch (err) {
    showAlert(err.message, "error");
  }
  btn.disabled = false;
  btn.textContent = "Connect sandbox bank";
}

async function openPlaidLink() {
  const btn = document.getElementById("plaid-link-btn");
  btn.disabled = true;
  btn.textContent = "Loading Plaid...";

  try {
    // Get a fresh link token from our backend
    const data = await apiGet("/plaid/create_link_token");
    const linkToken = data.link_token;

    // Open the Plaid Link modal — Plaid handles all the bank credential flow
    const handler = Plaid.create({
      token: linkToken,
      onSuccess: async (public_token, metadata) => {
        try {
          const institution = metadata.institution?.name || "Bank";
          const res = await apiPost("/plaid/exchange_public_token", {
            public_token,
            institution_name: institution,
          });
          showAlert(`${institution} connected! Synced ${res.etl.transactions.inserted} transactions.`, "success");
          loadAccounts();
        } catch (err) {
          showAlert(err.message, "error");
        }
      },
      onExit: (err) => {
        if (err) showAlert("Plaid connection failed: " + err.display_message, "error");
        btn.disabled = false;
        btn.textContent = "Connect real bank";
      },
    });

    handler.open();

  } catch (err) {
    showAlert("Could not open Plaid: " + err.message, "error");
    btn.disabled = false;
    btn.textContent = "Connect real bank";
  }
}

async function syncAll() {
  const btn = document.getElementById("sync-btn");
  btn.disabled = true;
  btn.textContent = "Syncing...";
  try {
    const data = await apiPost("/plaid/sync");
    showAlert(`Sync complete. ${data.stats.transactions_inserted} new transactions imported.`, "success");
    loadAccounts();
  } catch (err) {
    showAlert(err.message, "error");
  }
  btn.disabled = false;
  btn.textContent = "🔄 Sync all";
}
