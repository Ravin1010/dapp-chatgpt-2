import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "transactions.db")))
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "").strip()
CHAIN_ID = int(os.getenv("CHAIN_ID", "11155111"))
CHAIN_NAME = os.getenv("CHAIN_NAME", "Sepolia")

CONTRACT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "eventId", "type": "uint256"},
            {"indexed": False, "internalType": "string", "name": "name", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "eventTime", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "organizer", "type": "address"}
        ],
        "name": "EventCreated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "eventId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "attendee", "type": "address"}
        ],
        "name": "Registered",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "eventId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "attendee", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "CheckedIn",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "eventId", "type": "uint256"},
            {"indexed": False, "internalType": "bool", "name": "active", "type": "bool"}
        ],
        "name": "EventStatusChanged",
        "type": "event"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "name", "type": "string"},
            {"internalType": "uint256", "name": "eventTime", "type": "uint256"}
        ],
        "name": "createEvent",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "eventCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "eventId", "type": "uint256"}],
        "name": "getEvent",
        "outputs": [
            {
                "components": [
                    {"internalType": "uint256", "name": "id", "type": "uint256"},
                    {"internalType": "string", "name": "name", "type": "string"},
                    {"internalType": "uint256", "name": "eventTime", "type": "uint256"},
                    {"internalType": "address", "name": "organizer", "type": "address"},
                    {"internalType": "uint256", "name": "registeredCount", "type": "uint256"},
                    {"internalType": "uint256", "name": "checkedInCount", "type": "uint256"},
                    {"internalType": "bool", "name": "active", "type": "bool"}
                ],
                "internalType": "struct BlockCheck.EventInfo",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "eventId", "type": "uint256"}],
        "name": "getMyStatus",
        "outputs": [
            {"internalType": "bool", "name": "registered", "type": "bool"},
            {"internalType": "bool", "name": "checkedIn", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "eventId", "type": "uint256"},
            {"internalType": "address", "name": "user", "type": "address"}
        ],
        "name": "getUserStatus",
        "outputs": [
            {"internalType": "bool", "name": "registered", "type": "bool"},
            {"internalType": "bool", "name": "checkedIn", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "eventId", "type": "uint256"}],
        "name": "register",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "eventId", "type": "uint256"}],
        "name": "checkIn",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "eventId", "type": "uint256"},
            {"internalType": "bool", "name": "active", "type": "bool"}
        ],
        "name": "setEventActive",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

ALLOWED_ACTIONS = {
    "CREATE_EVENT",
    "REGISTER",
    "CHECK_IN",
    "CLOSE_EVENT",
    "REOPEN_EVENT",
}


def get_db_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_address TEXT NOT NULL,
            tx_hash TEXT NOT NULL UNIQUE,
            action TEXT NOT NULL,
            event_id INTEGER,
            details TEXT,
            block_number INTEGER,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_wallet ON transactions(wallet_address)"
    )
    conn.commit()
    conn.close()


# Idempotent: creates the SQLite database/table only if they do not already exist.
init_db()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/transactions")
def transactions_page():
    return render_template("transactions.html")


@app.get("/database")
def database_page():
    exists = DB_PATH.exists()
    row_count = 0
    if exists:
        conn = get_db_connection()
        try:
            row = conn.execute("SELECT COUNT(*) AS count FROM transactions").fetchone()
            row_count = row["count"] if row else 0
        except sqlite3.OperationalError:
            row_count = 0
        finally:
            conn.close()

    return render_template(
        "database.html",
        db_exists=exists,
        row_count=row_count,
        database_path=str(DB_PATH),
    )


@app.post("/database/create")
def create_database():
    existed_before = DB_PATH.exists()
    init_db()
    message = (
        "Database already exists. No duplicate database was created."
        if existed_before
        else "Database created successfully."
    )
    return render_template("message.html", title="Database", message=message)


@app.post("/database/delete")
def delete_database():
    if DB_PATH.exists():
        DB_PATH.unlink()
        message = "Database deleted successfully."
    else:
        message = "Database does not exist."
    return render_template("message.html", title="Database", message=message)


@app.get("/api/config")
def config():
    return jsonify({
        "contractAddress": CONTRACT_ADDRESS,
        "chainId": CHAIN_ID,
        "chainName": CHAIN_NAME,
        "abi": CONTRACT_ABI,
        "configured": bool(CONTRACT_ADDRESS),
    })


@app.post("/api/transactions")
def insert_transaction():
    data = request.get_json(silent=True) or {}

    wallet_address = str(data.get("walletAddress", "")).strip().lower()
    tx_hash = str(data.get("txHash", "")).strip().lower()
    action = str(data.get("action", "")).strip().upper()
    details = str(data.get("details", "")).strip()[:250]
    event_id_raw = data.get("eventId")
    block_number_raw = data.get("blockNumber")

    if not wallet_address.startswith("0x") or len(wallet_address) != 42:
        return jsonify({"ok": False, "error": "Invalid wallet address."}), 400
    if not tx_hash.startswith("0x") or len(tx_hash) != 66:
        return jsonify({"ok": False, "error": "Invalid transaction hash."}), 400
    if action not in ALLOWED_ACTIONS:
        return jsonify({"ok": False, "error": "Invalid transaction action."}), 400

    try:
        event_id = int(event_id_raw) if event_id_raw is not None else None
        block_number = int(block_number_raw) if block_number_raw is not None else None
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid event or block number."}), 400

    init_db()
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO transactions
                (wallet_address, tx_hash, action, event_id, details, block_number, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                wallet_address,
                tx_hash,
                action,
                event_id,
                details,
                block_number,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"ok": False, "error": "Transaction already recorded."}), 409
    finally:
        conn.close()

    return jsonify({"ok": True, "message": "Transaction saved."}), 201


@app.get("/api/transactions/<wallet_address>")
def get_transactions(wallet_address):
    wallet = wallet_address.strip().lower()
    if not wallet.startswith("0x") or len(wallet) != 42:
        return jsonify({"ok": False, "error": "Invalid wallet address."}), 400

    init_db()
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT id, wallet_address, tx_hash, action, event_id, details, block_number, created_at
        FROM transactions
        WHERE wallet_address = ?
        ORDER BY id DESC
        """,
        (wallet,),
    ).fetchall()
    conn.close()

    return jsonify({"ok": True, "transactions": [dict(row) for row in rows]})


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "app": "BlockCheck"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
