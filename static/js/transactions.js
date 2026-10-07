let config = null;
let walletAddress = null;

const connectBtn = document.getElementById("connectBtn");
const refreshBtn = document.getElementById("refreshBtn");
const transactionList = document.getElementById("transactionList");
const statusMessage = document.getElementById("statusMessage");
const walletBadge = document.getElementById("walletBadge");
const networkBadge = document.getElementById("networkBadge");

function setStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.classList.toggle("error", isError);
}

function shortAddress(address) {
  return address ? `${address.slice(0, 6)}…${address.slice(-4)}` : "—";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatSavedTime(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function actionLabel(action) {
  return {
    CREATE_EVENT: "Create Event",
    REGISTER: "Register",
    CHECK_IN: "Check In",
    CLOSE_EVENT: "Close Event",
    REOPEN_EVENT: "Reopen Event",
  }[action] || action;
}

async function loadConfig() {
  const response = await fetch("/api/config");
  if (!response.ok) throw new Error("Could not load DApp configuration.");
  config = await response.json();
  networkBadge.textContent = `Network: ${config.chainName}`;
}

async function connectWallet() {
  if (!window.ethereum) {
    setStatus("MetaMask is required to identify your wallet.", true);
    return;
  }

  try {
    const provider = new ethers.BrowserProvider(window.ethereum);
    await provider.send("eth_requestAccounts", []);
    const signer = await provider.getSigner();
    walletAddress = await signer.getAddress();

    walletBadge.textContent = `Wallet: ${shortAddress(walletAddress)}`;
    connectBtn.textContent = "Wallet Connected";
    refreshBtn.disabled = false;
    await loadTransactions();
  } catch (error) {
    setStatus(error.shortMessage || error.message || "Wallet connection failed.", true);
  }
}

async function loadTransactions() {
  if (!walletAddress) {
    transactionList.innerHTML = '<div class="empty-state">Connect your wallet to view your transactions.</div>';
    return;
  }

  try {
    setStatus("Loading transaction history…");
    const response = await fetch(`/api/transactions/${walletAddress}`);
    const result = await response.json();

    if (!response.ok) throw new Error(result.error || "Could not load transaction history.");

    if (!result.transactions.length) {
      transactionList.innerHTML = '<div class="empty-state">No saved transactions for this wallet yet.</div>';
      setStatus("No saved transactions found.");
      return;
    }

    transactionList.innerHTML = result.transactions.map((tx) => `
      <article class="transaction-card">
        <div class="transaction-top">
          <strong>${escapeHtml(actionLabel(tx.action))}</strong>
          ${tx.event_id !== null ? `<span class="state-pill">Event #${escapeHtml(tx.event_id)}</span>` : ""}
        </div>
        <div class="meta">
          ${tx.details ? `<div><strong>Details:</strong> ${escapeHtml(tx.details)}</div>` : ""}
          <div><strong>Transaction hash:</strong> <code>${escapeHtml(tx.tx_hash)}</code></div>
          ${tx.block_number !== null ? `<div><strong>Block:</strong> ${escapeHtml(tx.block_number)}</div>` : ""}
          <div><strong>Saved:</strong> ${escapeHtml(formatSavedTime(tx.created_at))}</div>
        </div>
      </article>
    `).join("");

    setStatus(`${result.transactions.length} transaction${result.transactions.length === 1 ? "" : "s"} loaded.`);
  } catch (error) {
    transactionList.innerHTML = '<div class="empty-state">Could not load transaction history.</div>';
    setStatus(error.message || "Could not load transaction history.", true);
  }
}

connectBtn.addEventListener("click", connectWallet);
refreshBtn.addEventListener("click", loadTransactions);

if (window.ethereum) {
  window.ethereum.on?.("accountsChanged", () => window.location.reload());
}

(async function boot() {
  try {
    await loadConfig();
    if (window.ethereum) {
      const accounts = await window.ethereum.request({ method: "eth_accounts" });
      if (accounts.length) {
        walletAddress = accounts[0];
        walletBadge.textContent = `Wallet: ${shortAddress(walletAddress)}`;
        connectBtn.textContent = "Wallet Connected";
        refreshBtn.disabled = false;
        await loadTransactions();
      }
    }
  } catch (error) {
    setStatus(error.message || "Page setup failed.", true);
  }
})();
