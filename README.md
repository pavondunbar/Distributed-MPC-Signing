# MPC Threshold Signing Network (Python)

> **SANDBOX / EDUCATIONAL USE ONLY — NOT FOR PRODUCTION**
>
> This codebase is a reference implementation designed for learning, prototyping, and architectural exploration of **multi-party computation (MPC)** and **threshold signature systems** in financial-grade infrastructure. It is **not cryptographically secure for production use**, not audited, and must not be used for real custody, key management, or settlement signing.

---

## Table of Contents

- [Overview](#overview)
- [What is MPC Threshold Signing?](#what-is-mpc-threshold-signing)
- [Architecture](#architecture)
- [Core Services](#core-services)
- [Key Features & Design Patterns](#key-features--design-patterns)
- [Event Timeline & Observability](#event-timeline--observability)
- [Failure Mode Simulation](#failure-mode-simulation)
- [Running in a Sandbox Environment](#running-in-a-sandbox-environment)
- [Project Structure](#project-structure)
- [Production Warning](#production-warning)
- [License](#license)

---

## Overview

The **MPC Threshold Signing Network** is a Python-based distributed system that simulates **2-of-3 threshold signature generation** using multiple independent signing nodes and a centralized coordinator.

It models how institutional-grade custody and settlement systems operate in environments such as MPC custody networks and threshold-signature workflows used in financial infrastructure.

The system demonstrates how signing can be decomposed into independent partial signature generation, coordinator aggregation, threshold recombination, and failure-resilient workflow orchestration.

---

## What is MPC Threshold Signing?

Multi-party computation threshold signing is a cryptographic architecture where no single node holds the full private key, each node holds a key shard, each node produces a partial signature, and a threshold such as 2-of-3 is required to produce a valid final signature.

### Conceptual Model

```text
        ┌──────────────┐
        │  Coordinator  │
        └──────┬───────┘
               │ fan-out
 ┌─────────────┼─────────────┐
 ▼             ▼             ▼
┌────────┐ ┌────────┐ ┌────────┐
│ Node 1 │ │ Node 2 │ │ Node 3 │
└────────┘ └────────┘ └────────┘
    │           │           │
    └──────┬────┴──────┬────┘
           ▼           ▼
     Partial Signatures
           │
           ▼
 Aggregated Threshold Signature
```

### Real-world analogy

This is analogous to institutional custody signing, cold storage approval workflows, and settlement authorization systems where multiple parties must authorize a transaction.

---

## Architecture

```text
                ┌────────────────────────────┐
                │      CLIENT REQUESTS       │
                │   (curl / API clients)      │
                └────────────┬───────────────┘
                             │
                             ▼
                ┌────────────────────────────┐
                │   MPC COORDINATOR (9000)   │
                │  /partial /result /timeline │
                └───────┬─────────┬──────────┘
                        │         │
        fan-out partial │         │ event tracking
                        ▼         ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐
    │  NODE 1    │ │  NODE 2    │ │  NODE 3    │
    │ port 8001  │ │ port 8002  │ │ port 8003  │
    └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
          │              │              │
     partial        partial          optional fail
          │              │              │
          └──────┬───────┴───────┬──────┘
                 ▼               ▼
        Coordinator aggregation layer
```

The coordinator sits at the center of the flow, collecting partial signatures, tracking session state, and producing the final aggregated result.

---

## Core Services

### `MPC Nodes (node-1 / node-2 / node-3)`

Each node performs deterministic partial signature generation from its node ID, session ID, and message hash. This design is useful for a sandbox because it is reproducible and easy to inspect, but it is not real threshold cryptography.

**Responsibilities:**
- Generate partial signatures.
- Simulate secure key shard operation.
- Optionally simulate node failure.

### `Coordinator (FastAPI, port 9000)`

The coordinator is responsible for receiving partial signatures, tracking session state, deterministically aggregating signatures, returning the final threshold signature, and emitting system-wide events for observability.

**State tracked:**
- Partial signatures per session.
- Node contributions.
- Completion status.

### `Signing Flow Endpoint`

`POST /partial` handles partial signature ingestion, session initialization, threshold evaluation, and aggregation execution.

### `Result Endpoint`

`GET /result/{session_id}` returns session status, partial count, and the aggregated signature if the threshold is complete.

---

## Key Features & Design Patterns

### Deterministic Signature Aggregation

Instead of real cryptographic combination, this system uses a deterministic aggregation rule over sorted partial signatures. That makes the result reproducible for demos and independent of arrival order.

This pattern is useful for illustrating orchestration logic, but it is not a substitute for a real threshold signature scheme such as ECDSA thresholding or distributed Schnorr-style protocols.

### Stateless Node Design

Each node has no shared memory, derives output purely from input, can be horizontally scaled, and can fail independently. That maps well to distributed-system teaching examples and fault-isolation demos.

### Coordinator as System-of-Record

The coordinator acts as the session state manager, aggregation engine, event emitter, and observability source of truth. This mirrors the control-plane role seen in many distributed signing and custody architectures.

---

## Event Timeline & Observability

The system includes a full event timeline log per session, which makes it suitable for debugging distributed signing flows and reconstructing audit-style traces.

### Event Store

```python
EVENT_LOG[session_id] = [
    {
        "timestamp": 1710000000.1,
        "event": "partial_received",
        "node_id": "node-1"
    }
]
```

### Instrumented Events

| Event | Description |
|---|---|
| `partial_received` | Node contributed partial signature. |
| `threshold_reached` | 2-of-3 threshold achieved. |
| `signature_finalized` | Final aggregation completed. |

### Timeline API

`GET /timeline/{session_id}` returns the chronological event stream for a signing session.

Example output:

```json
[
  {"event": "partial_received", "node_id": "node-1"},
  {"event": "partial_received", "node_id": "node-2"},
  {"event": "threshold_reached"},
  {"event": "signature_finalized"}
]
```

This supports real-time observability, debugging, and trace reconstruction across signing sessions.

---

## Failure Mode Simulation

The system includes intentional node failure simulation to demonstrate resilience patterns in distributed signing.

### Failure Injection

Configured via environment variable:

```bash
FAIL_NODE=node-3
```

### Behavior

If a node matches `FAIL_NODE`, it raises a simulated exception and does not contribute a partial signature.

### Resulting System Behavior

Even with one failed node, the system continues operating as long as the remaining nodes meet the threshold. In a 2-of-3 setup, the final signature can still be produced when two nodes succeed.

### Example Scenario

| Node | Status |
|---|---|
| node-1 | OK |
| node-2 | OK |
| node-3 | FAILED |

**Result:** the system succeeds, the coordinator reaches threshold, and the final signature is still produced.

This models fault tolerance in custody systems, partial quorum signing, and operational resilience.

---

## Running in a Sandbox Environment

### Option A: Docker Compose

```bash
docker compose up --build
```

### Services

| Service | Port | Description |
|---|---:|---|
| coordinator | 9000 | Aggregation + event store |
| node-1 | 8001 | MPC partial signer |
| node-2 | 8002 | MPC partial signer |
| node-3 | 8003 | MPC partial signer (optional failure) |

### Example Flow

1. Submit a signature request to `node-1`.

```bash
curl -X POST http://localhost:8001/api/sign \
  -H "Content-Type: application/json" \
  -d '{"session_id":"sig1","message_hash":"0xabc"}'
```

2. Submit to `node-2`.

```bash
curl -X POST http://localhost:8002/api/sign \
  -H "Content-Type: application/json" \
  -d '{"session_id":"sig1","message_hash":"0xabc"}'
```

3. Check result.

```bash
curl http://localhost:9000/result/sig1
```

4. View timeline.

```bash
curl http://localhost:9000/timeline/sig1
```

---

## Project Structure

```text
mpc-system/
│
├── coordinator/
│   └── app.py              # Aggregation + event store
│
├── mpc-node/
│   └── app/
│       └── main.py         # Partial signature generator
│
├── docker-compose.yml      # 3-node MPC cluster
└── README.md
```

The layout separates the control plane from the signer nodes, which is a clean way to teach distributed systems design and threshold-signing orchestration.

---

## Production Warning

This system is **not production-ready** and lacks critical security controls.

| Missing Component | Risk |
|---|---|
| Real MPC cryptography (FROST / GG20 / ECDSA threshold schemes) | Private key compromise. |
| HSM-backed key storage | Software key exposure. |
| Secure enclaves (SGX / Nitro Enclaves) | Node impersonation risk. |
| Network authentication (mTLS) | Unauthorized node participation. |
| Byzantine fault tolerance | Malicious node behavior unhandled. |
| Signature verification layer | No cryptographic validation. |
| Rate limiting / replay protection | Request replay attacks possible. |
| Key rotation system | Long-lived key shard exposure. |
| Audit-grade logging system | Simplified event logs only. |

This is a simulation of MPC architecture, not a secure cryptographic implementation.

---

## License

MIT — for educational and research purposes only.

Built with ❤️ by Pavon Dunbar — MPC and institutional systems simulation for distributed signing, custody, and settlement infrastructure learning.
