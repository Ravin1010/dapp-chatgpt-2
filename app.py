import os
from flask import Flask, jsonify, render_template

app = Flask(__name__)

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


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/config")
def config():
    return jsonify({
        "contractAddress": CONTRACT_ADDRESS,
        "chainId": CHAIN_ID,
        "chainName": CHAIN_NAME,
        "abi": CONTRACT_ABI,
        "configured": bool(CONTRACT_ADDRESS),
    })


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "app": "BlockCheck"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
