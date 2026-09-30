# BlockCheck

BlockCheck is a mobile-friendly blockchain event registration and attendance DApp.

## Stack

- Solidity smart contract
- Remix for compilation/deployment
- Sepolia testnet
- HTML/CSS/JavaScript frontend
- ethers.js
- Flask backend
- Gunicorn
- Render hosting

## Main features

- Create an event on-chain
- Register with MetaMask
- Check in to an event
- Prevent duplicate registration
- Prevent duplicate check-in
- View total registrations and attendance
- Organizer can close/reopen an event
- Verify any wallet's registration/check-in status
- Mobile-responsive UI

## 1. Deploy the Solidity contract with Remix

Open Remix and create:

`BlockCheck.sol`

Paste the contents of:

`contracts/BlockCheck.sol`

Then:

1. Compile with Solidity 0.8.24.
2. Open **Deploy & Run Transactions**.
3. Choose **Injected Provider - MetaMask**.
4. Switch MetaMask to **Sepolia**.
5. Click **Deploy**.
6. Confirm the transaction.
7. Copy the deployed contract address.

There is no constructor input.

## 2. Local test

Install dependencies:

```bash
pip install -r requirements.txt
```

### Windows PowerShell

```powershell
$env:CONTRACT_ADDRESS="0xYOUR_CONTRACT_ADDRESS"
python app.py
```

### macOS/Linux

```bash
export CONTRACT_ADDRESS="0xYOUR_CONTRACT_ADDRESS"
python app.py
```

Open:

`http://127.0.0.1:5000`

## 3. Render deployment

Push this whole project to GitHub.

Create a new Render Web Service:

- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

Environment variables:

- `CONTRACT_ADDRESS` = the address deployed from Remix
- `CHAIN_ID` = `11155111`
- `CHAIN_NAME` = `Sepolia`

The included `render.yaml` already contains the service configuration.

## 4. Mobile use

The website is responsive.

For blockchain transactions on a phone:

1. Install/open MetaMask Mobile.
2. Switch to Sepolia.
3. Open the Render URL in MetaMask Mobile's built-in browser.
4. Connect wallet.
5. Register/check in.

If opened from a normal mobile browser without an injected wallet, the page shows an **Open in MetaMask Mobile** button.

## Demo flow

1. Wallet A creates an event.
2. Wallet B connects and registers.
3. Wallet B checks in.
4. The event's registered and checked-in counts update.
5. Enter Wallet B's address in the verification section to prove attendance.

## Important limitation

This classroom/demo version lets registered attendees check themselves in. It proves the wallet performed an on-chain check-in, but it does not prove physical presence at the venue. A production system could add organizer-signed QR check-in tokens or another physical-presence mechanism.

## Security

Never store wallet private keys or seed phrases in Flask, JavaScript, GitHub, or Render environment variables. Transactions are signed inside the user's wallet.
