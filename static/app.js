const config = window.DAPP_CONFIG;
const ABI = [
  "function makeTransaction(string note) payable",
  "event TransactionRecorded(address indexed user,uint256 amount,string note,uint256 timestamp)"
];

let provider;
let signer;
let walletAddress = "";

const walletStatus = document.getElementById("walletStatus");
const statusEl = document.getElementById("status");
const connectButton = document.getElementById("connectButton");
const sendButton = document.getElementById("sendButton");

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

async function connectWallet() {
  if (!window.ethereum) {
    setStatus("MetaMask is required.", true);
    return;
  }

  provider = new ethers.BrowserProvider(window.ethereum);
  await provider.send("eth_requestAccounts", []);

  const network = await provider.getNetwork();
  if (Number(network.chainId) !== Number(config.chainId)) {
    setStatus(`Please switch MetaMask to ${config.chainName}.`, true);
    return;
  }

  signer = await provider.getSigner();
  walletAddress = await signer.getAddress();
  walletStatus.textContent = walletAddress;
  connectButton.textContent = "Connected";
  setStatus("Wallet connected.");
}

async function sendAndSave() {
  try {
    if (!walletAddress) {
      await connectWallet();
    }
    if (!walletAddress) return;

    if (!config.contractAddress) {
      setStatus("Contract address is not configured yet.", true);
      return;
    }

    const amount = document.getElementById("amount").value.trim();
    const note = document.getElementById("note").value.trim();

    if (!amount || Number(amount) <= 0) {
      setStatus("Enter an ETH amount greater than zero.", true);
      return;
    }

    const contract = new ethers.Contract(config.contractAddress, ABI, signer);

    setStatus("Confirm the transaction in MetaMask...");
    const tx = await contract.makeTransaction(note, {
      value: ethers.parseEther(amount)
    });

    setStatus("Waiting for blockchain confirmation...");
    await tx.wait();

    setStatus("Confirmed. Saving transaction to SQLite...");
    const response = await fetch("/api/transactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        wallet_address: walletAddress,
        tx_hash: tx.hash,
        amount_eth: amount,
        note
      })
    });

    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "Could not save transaction");
    }

    setStatus(`Saved successfully. Tx: ${tx.hash}`);
  } catch (error) {
    console.error(error);
    setStatus(error.shortMessage || error.message || "Transaction failed", true);
  }
}

connectButton.addEventListener("click", connectWallet);
sendButton.addEventListener("click", sendAndSave);
