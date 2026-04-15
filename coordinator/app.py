from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

STATE = {}


class PartialSig(BaseModel):
    session_id: str
    node_id: str
    partial_signature: str


# -------------------------
# RECEIVE PARTIAL SIGS
# -------------------------
@app.post("/partial")
def partial(p: PartialSig):
    if p.session_id not in STATE:
        STATE[p.session_id] = {}

    STATE[p.session_id][p.node_id] = p.partial_signature

    return evaluate(p.session_id)


# -------------------------
# THRESHOLD EVALUATION
# -------------------------
def evaluate(session_id: str):
    sigs = STATE.get(session_id, {})
    count = len(sigs)

    if count >= 2:
        # "aggregation simulation"
        # (real MPC would combine mathematically here)
        full_signature = hash(
            tuple(sorted(sigs.values()))
        )

        return {
            "session_id": session_id,
            "status": "complete",
            "partial_count": count,
            "aggregated_signature": str(full_signature)
        }

    return {
        "session_id": session_id,
        "status": "pending",
        "partial_count": count
    }


# -------------------------
# VIEW RESULT
# -------------------------
@app.get("/result/{session_id}")
def result(session_id: str):
    return evaluate(session_id)
