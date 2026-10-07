# BlockCheck

BlockCheck is a mobile-friendly blockchain event registration and attendance DApp with SQLite-backed per-wallet transaction history.

## Stack

- Solidity smart contract
- Remix for compilation/deployment
- Sepolia testnet
- HTML/CSS/JavaScript frontend
- ethers.js
- Flask backend
- SQLite3 transaction database
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
- Save confirmed write transactions into SQLite
- View transaction history for the connected wallet
- Idempotent one-time database creation
- Delete the SQLite transaction-history database from the Database page
- Mobile-responsive UI

## SQLite transaction history

Every confirmed BlockCheck write is stored with:

- wallet address
- transaction hash
- action (`CREATE_EVENT`, `REGISTER`, `CHECK_IN`, `CLOSE_EVENT`, `REOPEN_EVENT`)
- event ID when applicable
- description/details
- block number
- UTC saved timestamp

`tx_hash` is unique, so the same blockchain transaction cannot be inserted twice.

The database file is `transactions.db` by default and is excluded from Git.

## 1. Deploy the Solidity contract with Remix

Open Remix and create `BlockCheck.sol`, using `contracts/BlockCheck.sol` from this repository.

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

```bash
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
$env:CONTRACT_ADDRESS="0xYOUR_CONTRACT_ADDRESS"
python app.py
```

macOS/Linux:

```bash
export CONTRACT_ADDRESS="0xYOUR_CONTRACT_ADDRESS"
python app.py
```

Open `http://127.0.0.1:5000`.

Useful pages:

- `/` — BlockCheck DApp
- `/transactions` — connected wallet's saved transactions
- `/database` — create/status/delete SQLite database

## 3. Render deployment

Create a Render Web Service with:

- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- `CONTRACT_ADDRESS` = deployed BlockCheck contract address
- `CHAIN_ID` = `11155111`
- `CHAIN_NAME` = `Sepolia`

### Important SQLite limitation on Render

On Render's free web-service plan, the local filesystem is ephemeral. `transactions.db` can be lost after service replacement/redeploy. For durable SQLite storage, attach a Render persistent disk and set `DATABASE_PATH` to a path on that disk. A persistent disk is a paid Render resource.

## 4. Mobile use

The website is responsive. For blockchain transactions on a phone, open the Render URL in MetaMask Mobile's built-in browser while connected to Sepolia.

## Demo flow

1. Wallet A creates an event.
2. Wallet B connects and registers.
3. Wallet B checks in.
4. Open **My Transactions** to show Wallet B's saved registration/check-in records.
5. Open **SQLite Database** to show the database status and record count.
6. Use **Delete Database** to demonstrate database deletion (this deletes only SQLite history, not blockchain transactions).

## Security

Never store wallet private keys or seed phrases in Flask, JavaScript, GitHub, or Render environment variables. Transactions are signed inside the user's wallet.
