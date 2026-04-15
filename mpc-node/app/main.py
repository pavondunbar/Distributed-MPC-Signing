from fastapi import FastAPI
from pydantic import BaseModel
import hashlib
import os

app = FastAPI()

NODE_ID = os.getenv("NODE_ID", "node-unknown")
COORDINATOR_URL = os.getenv("COORDINATOR_URL", "http://localhost:9000")


class SignRequest(BaseModel):
    session_id: str
    message_hash: str


# -------------------------
# HEALTH
# -------------------------
@app.get("/api/health")
def health():
    return {"node": NODE_ID, "status": "ok"}


# -------------------------
# PARTIAL SIGNATURE
# -------------------------
@app.post("/api/sign")
def sign(req: SignRequest):
    """
    Simulates partial signature generation.
    In real MPC this would be:
    - nonce commitment
    - ECDSA partial
    - share-based computation
    """

    partial = hashlib.sha256(
        f"{NODE_ID}:{req.session_id}:{req.message_hash}".encode()
    ).hexdigest()

    # send to coordinator
    import requests
    res = requests.post(
        f"{COORDINATOR_URL}/partial",
        json={
            "session_id": req.session_id,
            "node_id": NODE_ID,
            "partial_signature": partial
        }
    )

    return {
        "node": NODE_ID,
        "partial_signature": partial,
        "coordinator": res.json()
    }
