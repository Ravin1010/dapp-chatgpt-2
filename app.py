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


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_address TEXT NOT NULL,
            tx_hash TEXT NOT NULL UNIQUE,
            amount_eth TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_wallet ON transactions(wallet_address)"
    )
    conn.commit()
    conn.close()


# One-time/idempotent database creation on app startup.
init_db()


@app.get("/")
def index():
    return render_template(
        "index.html",
        contract_address=CONTRACT_ADDRESS,
        chain_id=CHAIN_ID,
        chain_name=CHAIN_NAME,
    )


@app.get("/transactions")
def transactions_page():
    return render_template(
        "transactions.html",
        contract_address=CONTRACT_ADDRESS,
        chain_id=CHAIN_ID,
        chain_name=CHAIN_NAME,
    )


@app.get("/database")
def database_page():
    exists = DB_PATH.exists()
    row_count = 0
    if exists:
        conn = get_connection()
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
        "Database already exists; no duplicate database was created."
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


@app.post("/api/transactions")
def insert_transaction():
    data = request.get_json(silent=True) or {}
    wallet = str(data.get("wallet_address", "")).strip().lower()
    tx_hash = str(data.get("tx_hash", "")).strip().lower()
    amount_eth = str(data.get("amount_eth", "")).strip()
    note = str(data.get("note", "")).strip()[:200]

    if not wallet.startswith("0x") or len(wallet) != 42:
        return jsonify({"ok": False, "error": "Invalid wallet address"}), 400
    if not tx_hash.startswith("0x") or len(tx_hash) != 66:
        return jsonify({"ok": False, "error": "Invalid transaction hash"}), 400
    if not amount_eth:
        return jsonify({"ok": False, "error": "Amount is required"}), 400

    init_db()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO transactions
                (wallet_address, tx_hash, amount_eth, note, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                wallet,
                tx_hash,
                amount_eth,
                note,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"ok": False, "error": "Transaction already recorded"}), 409
    finally:
        conn.close()

    return jsonify({"ok": True, "message": "Transaction saved"}), 201


@app.get("/api/transactions/<wallet_address>")
def get_transactions(wallet_address):
    wallet = wallet_address.strip().lower()
    if not wallet.startswith("0x") or len(wallet) != 42:
        return jsonify({"ok": False, "error": "Invalid wallet address"}), 400

    init_db()
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, wallet_address, tx_hash, amount_eth, note, created_at
        FROM transactions
        WHERE wallet_address = ?
        ORDER BY id DESC
        """,
        (wallet,),
    ).fetchall()
    conn.close()

    return jsonify({"ok": True, "transactions": [dict(row) for row in rows]})


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
