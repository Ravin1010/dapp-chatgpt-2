let config = null;
let provider = null;
let signer = null;
let contract = null;
let walletAddress = null;

const connectBtn = document.getElementById("connectBtn");
const mobileWalletBtn = document.getElementById("mobileWalletBtn");
const createEventForm = document.getElementById("createEventForm");
const createBtn = document.getElementById("createBtn");
const refreshBtn = document.getElementById("refreshBtn");
const eventList = document.getElementById("eventList");
const statusMessage = document.getElementById("statusMessage");
const setupWarning = document.getElementById("setupWarning");
const verifyForm = document.getElementById("verifyForm");
const verifyResult = document.getElementById("verifyResult");

function setStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.classList.toggle("error", isError);
}

function shortAddress(address) {
  return address ? `${address.slice(0, 6)}…${address.slice(-4)}` : "—";
}

function isMobile() {
  return /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
}

function showMobileWalletFallback() {
  if (!window.ethereum && isMobile()) {
    mobileWalletBtn.classList.remove("hidden");
  }
}

function openInMetaMaskMobile() {
  const path = `${window.location.host}${window.location.pathname}`;
  window.location.href = `https://metamask.app.link/dapp/${path}`;
}

function formatDate(unixSeconds) {
  return new Date(Number(unixSeconds) * 1000).toLocaleString();
}

async function loadConfig() {
  const response = await fetch("/api/config");
  if (!response.ok) throw new Error("Could not load DApp configuration.");

  config = await response.json();
  document.getElementById("networkBadge").textContent = `Network: ${config.chainName}`;

  if (!config.configured) {
    setupWarning.classList.remove("hidden");
    createBtn.disabled = true;
    refreshBtn.disabled = true;
  }
}

async function ensureCorrectNetwork() {
  const network = await provider.getNetwork();
  const expected = BigInt(config.chainId);

  if (network.chainId === expected) return;

  const hexChainId = `0x${Number(config.chainId).toString(16)}`;

  try {
    await window.ethereum.request({
      method: "wallet_switchEthereumChain",
      params: [{ chainId: hexChainId }],
    });

    provider = new ethers.BrowserProvider(window.ethereum);
    signer = await provider.getSigner();
  } catch {
    throw new Error(`Please switch MetaMask to ${config.chainName}.`);
  }
}

async function connectWallet() {
  if (!config?.configured) {
    setStatus("Deploy BlockCheck.sol and configure CONTRACT_ADDRESS first.", true);
    return;
  }

  if (!window.ethereum) {
    showMobileWalletFallback();
    setStatus("MetaMask not detected. On mobile, open this page inside MetaMask Mobile.", true);
    return;
  }

  try {
    setStatus("Connecting wallet…");
    provider = new ethers.BrowserProvider(window.ethereum);
    await provider.send("eth_requestAccounts", []);
    await ensureCorrectNetwork();

    signer = await provider.getSigner();
    walletAddress = await signer.getAddress();
    contract = new ethers.Contract(config.contractAddress, config.abi, signer);

    document.getElementById("walletBadge").textContent = `Wallet: ${shortAddress(walletAddress)}`;
    connectBtn.textContent = "Wallet Connected";

    await loadEvents();
    setStatus("Wallet connected.");
  } catch (error) {
    setStatus(error.shortMessage || error.message || "Wallet connection failed.", true);
  }
}

async function createEvent(event) {
  event.preventDefault();

  if (!contract) {
    setStatus("Connect your wallet first.", true);
    return;
  }

  const name = document.getElementById("eventName").value.trim();
  const timeValue = document.getElementById("eventTime").value;

  if (!name || !timeValue) {
    setStatus("Enter the event name and date/time.", true);
    return;
  }

  const timestamp = Math.floor(new Date(timeValue).getTime() / 1000);

  if (!Number.isFinite(timestamp) || timestamp <= Math.floor(Date.now() / 1000)) {
    setStatus("Event date/time must be in the future.", true);
    return;
  }

  try {
    createBtn.disabled = true;
    createBtn.textContent = "Confirm in MetaMask…";
    setStatus("Waiting for wallet confirmation…");

    const tx = await contract.createEvent(name, timestamp);

    createBtn.textContent = "Waiting for block…";
    setStatus(`Transaction sent: ${tx.hash.slice(0, 12)}…`);

    await tx.wait();

    createEventForm.reset();
    await loadEvents();
    setStatus("Event created successfully.");
  } catch (error) {
    setStatus(error.shortMessage || error.reason || error.message || "Could not create event.", true);
  } finally {
    createBtn.disabled = false;
    createBtn.textContent = "Create Event On-Chain";
  }
}

async function registerForEvent(eventId) {
  if (!contract) return;

  try {
    setStatus(`Registering for event #${eventId}…`);
    const tx = await contract.register(eventId);
    await tx.wait();
    await loadEvents();
    setStatus(`Registered for event #${eventId}.`);
  } catch (error) {
    setStatus(error.shortMessage || error.reason || error.message || "Registration failed.", true);
  }
}

async function checkInToEvent(eventId) {
  if (!contract) return;

  try {
    setStatus(`Checking in to event #${eventId}…`);
    const tx = await contract.checkIn(eventId);
    await tx.wait();
    await loadEvents();
    setStatus(`Checked in to event #${eventId}.`);
  } catch (error) {
    setStatus(error.shortMessage || error.reason || error.message || "Check-in failed.", true);
  }
}

async function setEventActive(eventId, active) {
  if (!contract) return;

  try {
    setStatus(`${active ? "Activating" : "Closing"} event #${eventId}…`);
    const tx = await contract.setEventActive(eventId, active);
    await tx.wait();
    await loadEvents();
    setStatus(`Event #${eventId} updated.`);
  } catch (error) {
    setStatus(error.shortMessage || error.reason || error.message || "Could not update event.", true);
  }
}

async function loadEvents() {
  if (!contract) {
    eventList.innerHTML = '<div class="empty-state">Connect your wallet to load events.</div>';
    return;
  }

  try {
    setStatus("Loading events…");
    const count = Number(await contract.eventCount());

    if (count === 0) {
      eventList.innerHTML = '<div class="empty-state">No events yet. Create the first one.</div>';
      setStatus("No events found.");
      return;
    }

    const cards = [];

    // Newest event first.
    for (let id = count; id >= 1; id--) {
      const info = await contract["getEvent(uint256)"](id);
      const [registered, checkedIn] = await contract.getMyStatus(id);

      const isOrganizer =
        walletAddress &&
        info.organizer.toLowerCase() === walletAddress.toLowerCase();

      cards.push(`
        <article class="event-card">
          <div class="event-top">
            <div>
              <h3>${escapeHtml(info.name)}</h3>
              <div class="event-id">Event #${id}</div>
            </div>
            <span class="state-pill ${info.active ? "" : "inactive"}">
              ${info.active ? "Active" : "Closed"}
            </span>
          </div>

          <div class="meta">
            <div><strong>Date:</strong> ${formatDate(info.eventTime)}</div>
            <div><strong>Organizer:</strong> ${shortAddress(info.organizer)}</div>
            <div><strong>Registered:</strong> ${info.registeredCount.toString()}</div>
            <div><strong>Checked in:</strong> ${info.checkedInCount.toString()}</div>
          </div>

          <div class="user-status">
            Your status:
            ${registered ? "✅ Registered" : "⬜ Not registered"}
            ·
            ${checkedIn ? "✅ Checked in" : "⬜ Not checked in"}
          </div>

          <div class="event-actions">
            <button
              class="button primary"
              onclick="registerForEvent(${id})"
              ${registered || !info.active ? "disabled" : ""}
            >
              ${registered ? "Registered" : "Register"}
            </button>

            <button
              class="button secondary"
              onclick="checkInToEvent(${id})"
              ${!registered || checkedIn || !info.active ? "disabled" : ""}
            >
              ${checkedIn ? "Checked In" : "Check In"}
            </button>

            ${
              isOrganizer
                ? `<button
                     class="button secondary"
                     onclick="setEventActive(${id}, ${!info.active})"
                   >
                     ${info.active ? "Close Event" : "Reopen Event"}
                   </button>`
                : ""
            }
          </div>
        </article>
      `);
    }

    eventList.innerHTML = cards.join("");
    setStatus(`${count} event${count === 1 ? "" : "s"} loaded.`);
  } catch (error) {
    eventList.innerHTML = '<div class="empty-state">Could not load events.</div>';
    setStatus(error.shortMessage || error.message || "Could not load events.", true);
  }
}

async function verifyAttendance(event) {
  event.preventDefault();

  if (!contract) {
    setStatus("Connect your wallet first.", true);
    return;
  }

  const eventId = Number(document.getElementById("verifyEventId").value);
  const address = document.getElementById("verifyWallet").value.trim();

  if (!ethers.isAddress(address)) {
    setStatus("Enter a valid Ethereum wallet address.", true);
    return;
  }

  try {
    const [registered, checkedIn] = await contract.getUserStatus(eventId, address);

    verifyResult.classList.remove("hidden");
    verifyResult.innerHTML = `
      <strong>Wallet:</strong> ${escapeHtml(address)}<br>
      <strong>Registered:</strong> ${registered ? "Yes ✅" : "No ❌"}<br>
      <strong>Checked in:</strong> ${checkedIn ? "Yes ✅" : "No ❌"}
    `;

    setStatus("Attendance status verified from the blockchain.");
  } catch (error) {
    verifyResult.classList.add("hidden");
    setStatus(error.shortMessage || error.reason || error.message || "Verification failed.", true);
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

connectBtn.addEventListener("click", connectWallet);
mobileWalletBtn.addEventListener("click", openInMetaMaskMobile);
createEventForm.addEventListener("submit", createEvent);
refreshBtn.addEventListener("click", loadEvents);
verifyForm.addEventListener("submit", verifyAttendance);

window.registerForEvent = registerForEvent;
window.checkInToEvent = checkInToEvent;
window.setEventActive = setEventActive;

if (window.ethereum) {
  window.ethereum.on?.("accountsChanged", () => window.location.reload());
  window.ethereum.on?.("chainChanged", () => window.location.reload());
}

(async function boot() {
  try {
    await loadConfig();
    showMobileWalletFallback();
  } catch (error) {
    setStatus(error.message || "App setup failed.", true);
  }
})();
