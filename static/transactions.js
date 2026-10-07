let walletAddress = "";

const walletStatus = document.getElementById("walletStatus");
const connectButton = document.getElementById("connectButton");
const refreshButton = document.getElementById("refreshButton");
const list = document.getElementById("transactionsList");

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

async function connectWallet() {
  if (!window.ethereum) {
    list.innerHTML = "<p class='error'>MetaMask is required.</p>";
    return;
  }

  const provider = new ethers.BrowserProvider(window.ethereum);
  await provider.send("eth_requestAccounts", []);
  const signer = await provider.getSigner();
  walletAddress = await signer.getAddress();
  walletStatus.textContent = walletAddress;
  connectButton.textContent = "Connected";
  await loadTransactions();
}

async function loadTransactions() {
  if (!walletAddress) {
    list.innerHTML = "<p>Connect your wallet to load transactions.</p>";
    return;
  }

  list.innerHTML = "<p>Loading...</p>";
  const response = await fetch(`/api/transactions/${walletAddress}`);
  const result = await response.json();

  if (!response.ok) {
    list.innerHTML = `<p class='error'>${escapeHtml(result.error || "Could not load transactions")}</p>`;
    return;
  }

  if (!result.transactions.length) {
    list.innerHTML = "<p>No saved transactions for this wallet yet.</p>";
    return;
  }

  list.innerHTML = result.transactions.map((tx) => `
    <article class="transaction-item">
      <div><strong>Amount:</strong> ${escapeHtml(tx.amount_eth)} ETH</div>
      <div><strong>Note:</strong> ${escapeHtml(tx.note || "-")}</div>
      <div><strong>Hash:</strong> <code>${escapeHtml(tx.tx_hash)}</code></div>
      <div><strong>Saved:</strong> ${escapeHtml(tx.created_at)}</div>
    </article>
  `).join("");
}

connectButton.addEventListener("click", connectWallet);
refreshButton.addEventListener("click", loadTransactions);
