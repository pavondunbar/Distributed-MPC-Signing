from fastapi import FastAPI
from pydantic import BaseModel
import hashlib
import os
import requests

app = FastAPI()

# -------------------------
# ENV CONFIG
# -------------------------
NODE_ID = os.getenv("NODE_ID", "node-unknown")
COORDINATOR_URL = os.getenv("COORDINATOR_URL", "http://localhost:9000")

# STEP 4: FAILURE MODE FLAG
FAIL_NODE = os.getenv("FAIL_NODE", None)


# -------------------------
# REQUEST MODEL
# -------------------------
class SignRequest(BaseModel):
    session_id: str
    message_hash: str


# -------------------------
# HEALTH CHECK
# -------------------------
@app.get("/api/health")
def health():
    return {
        "node": NODE_ID,
        "status": "ok",
        "fail_mode_enabled": FAIL_NODE == NODE_ID
    }


# -------------------------
# PARTIAL SIGNATURE GENERATION
# -------------------------
@app.post("/api/sign")
def sign(req: SignRequest):

    # -------------------------------------------------
    # STEP 4: FAILURE INJECTION (NODE DROP SIMULATION)
    # -------------------------------------------------
    if FAIL_NODE and NODE_ID == FAIL_NODE:
        raise Exception(f"Simulated failure on {NODE_ID}")

    # -------------------------------------------------
    # DETERMINISTIC PARTIAL SIGNATURE (SHA-256)
    # -------------------------------------------------
    partial = hashlib.sha256(
        f"{NODE_ID}:{req.session_id}:{req.message_hash}".encode()
    ).hexdigest()

    # -------------------------------------------------
    # SEND TO COORDINATOR (FAILURE-RESILIENT)
    # -------------------------------------------------
    coordinator_response = None

    try:
        res = requests.post(
            f"{COORDINATOR_URL}/partial",
            json={
                "session_id": req.session_id,
                "node_id": NODE_ID,
                "partial_signature": partial
            },
            timeout=5
        )

        # safe parsing (avoid jq crashes / malformed responses)
        try:
            coordinator_response = res.json()
        except Exception:
            coordinator_response = {
                "error": "invalid_json_response",
                "raw": res.text
            }

    except requests.exceptions.Timeout:
        coordinator_response = {
            "error": "coordinator_timeout"
        }

    except requests.exceptions.ConnectionError:
        coordinator_response = {
            "error": "coordinator_unreachable"
        }

    except Exception as e:
        coordinator_response = {
            "error": "unknown_error",
            "detail": str(e)
        }

    # -------------------------------------------------
    # RESPONSE (DASHBOARD-FRIENDLY)
    # -------------------------------------------------
    return {
        "node": NODE_ID,
        "partial_signature": partial,
        "fail_mode_active": FAIL_NODE == NODE_ID,
        "coordinator": coordinator_response
    }
