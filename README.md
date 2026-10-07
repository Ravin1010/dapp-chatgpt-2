# SQLite Transaction DApp

Standalone DApp using Solidity + Flask + SQLite.

## Features
- Solidity smart contract (`contracts/TransactionLogger.sol`)
- MetaMask + ethers.js frontend
- Flask backend
- SQLite transaction database
- One-time/idempotent database creation
- Insert confirmed blockchain transactions
- View transaction history by connected wallet
- Delete the SQLite database from the database page
- Render-ready deployment

## Database
Table: `transactions`

Fields: `id`, `wallet_address`, `tx_hash`, `amount_eth`, `note`, `created_at`.

`tx_hash` is unique so the same blockchain transaction cannot be inserted twice.

## Deploy the contract
1. Open Remix.
2. Create `TransactionLogger.sol` and paste `contracts/TransactionLogger.sol`.
3. Compile with Solidity 0.8.24.
4. Deploy using Injected Provider - MetaMask on Sepolia.
5. Copy the deployed contract address.

## Render
Build command: `pip install -r requirements.txt`

Start command: `gunicorn app:app`

Environment variables:
- `CHAIN_ID=11155111`
- `CHAIN_NAME=Sepolia`
- `CONTRACT_ADDRESS=<deployed contract address>`

Important: free Render web-service storage is ephemeral, so SQLite may reset after redeploy/restart. A persistent Render disk is needed for durable SQLite storage.
