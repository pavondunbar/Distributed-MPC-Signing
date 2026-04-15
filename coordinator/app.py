from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Optional
import time
import hashlib

app = FastAPI()

# -------------------------
# STATE STORAGE
# -------------------------
STATE: Dict[str, Dict[str, str]] = {}

# -------------------------
# EVENT STREAM STORE (STEP 3)
# -------------------------
EVENT_LOG: Dict[str, List[dict]] = {}


# -------------------------
# MODELS
# -------------------------
class PartialSig(BaseModel):
    session_id: str
    node_id: str
    partial_signature: str


class VerifyRequest(BaseModel):
    session_id: str
    signature: str


# -------------------------
# EVENT EMITTER (STEP 3 IMPLEMENTATION)
# -------------------------
def emit_event(session_id: str, event: str, node_id: str = None):
    if session_id not in EVENT_LOG:
        EVENT_LOG[session_id] = []

    EVENT_LOG[session_id].append({
        "timestamp": time.time(),
        "event": event,
        "node_id": node_id
    })


# -------------------------
# DETERMINISTIC AGGREGATION (SHA-256)
# -------------------------
def compute_aggregated_signature(sigs: Dict[str, str]) -> str:
    ordered = sorted(sigs.values())
    payload = "|".join(ordered).encode()
    return hashlib.sha256(payload).hexdigest()


# -------------------------
# RECEIVE PARTIAL SIGS
# -------------------------
@app.post("/partial")
def partial(p: PartialSig):
    if p.session_id not in STATE:
        STATE[p.session_id] = {}
        emit_event(p.session_id, "session_created")

    # store partial
    STATE[p.session_id][p.node_id] = p.partial_signature

    # (1) STEP 3: instrument node contribution received
    emit_event(p.session_id, "partial_received", p.node_id)

    return evaluate(p.session_id)


# -------------------------
# THRESHOLD EVALUATION
# -------------------------
def evaluate(session_id: str):
    sigs = STATE.get(session_id, {})
    count = len(sigs)

    emit_event(session_id, "evaluation_check")

    if count >= 2:
        emit_event(session_id, "threshold_reached")

        full_signature = compute_aggregated_signature(sigs)

        # (3) STEP 3: finalization event
        emit_event(session_id, "signature_finalized")

        return {
            "session_id": session_id,
            "status": "complete",
            "partial_count": count,
            "aggregated_signature": full_signature
        }

    return {
        "session_id": session_id,
        "status": "pending",
        "partial_count": count
    }


# -------------------------
# RESULT ENDPOINT
# -------------------------
@app.get("/result/{session_id}")
def result(session_id: str):
    emit_event(session_id, "result_viewed")
    return evaluate(session_id)


# -------------------------
# TIMELINE STREAMING ENDPOINT (STEP 3 CORE)
# -------------------------
@app.get("/timeline/{session_id}")
def timeline(session_id: str):
    return EVENT_LOG.get(session_id, [])


# -------------------------
# SIGNATURE VERIFICATION MOCK
# -------------------------
@app.post("/verify")
def verify(payload: VerifyRequest):
    is_valid = (
        payload.signature is not None and
        len(payload.signature) > 10 and
        payload.session_id.startswith("sig")
    )

    emit_event(
        payload.session_id,
        "signature_verified" if is_valid else "signature_rejected"
    )

    return {
        "session_id": payload.session_id,
        "valid": is_valid,
        "mode": "mock_verifier_v1"
    }
