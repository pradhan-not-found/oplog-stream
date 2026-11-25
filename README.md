<div align="center">
  <img src="assets/banner.svg" alt="oplog-stream banner" width="100%"/>
</div>

<br/>

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-00ED64?style=flat-square&logo=mongodb&logoColor=white)](https://cloud.mongodb.com)
[![PyMongo](https://img.shields.io/badge/PyMongo-4.7.3-13AA52?style=flat-square)](https://pymongo.readthedocs.io)
[![Sessions](https://img.shields.io/badge/Concurrent%20Sessions-20-blueviolet?style=flat-square)]()
[![Docs](https://img.shields.io/badge/Docs%20Inserted-20%2C000-orange?style=flat-square)]()
[![Error Rate](https://img.shields.io/badge/Error%20Rate-0%25-brightgreen?style=flat-square)]()

</div>

<br/>

---

## Overview

**oplog-stream** stress-tests MongoDB Atlas by pushing **20-variable IoT telemetry documents** from **20 fully independent concurrent Python sessions**, while a separate pull consumer tails all new data in real time. The project benchmarks Atlas opcounters, oplog throughput, replication lag, and query performance under sustained parallel write load.

<br/>

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PUSH ENVIRONMENT                                                       │
│                                                                         │
│  launch_sessions.py                                                     │
│    ├─ Session 01 ─► push_script.py ──────────────────────────────┐     │
│    ├─ Session 02 ─► push_script.py ──────────────────────────────┤     │
│    │        ···                                                   │     │
│    └─ Session 20 ─► push_script.py ──────────────────────────────┤     │
│                                              insert_one() × 1000 │     │
└──────────────────────────────────────────────────────────────────┼─────┘
                                                                   │
                                               ┌───────────────────▼──────────┐
                                               │   MongoDB Atlas — Cluster0   │
                                               │   ┌─────────┐                │
                                               │   │ Primary │──► Oplog       │
                                               │   └────┬────┘  (capped col)  │
                                               │        ├──► Secondary 1       │
                                               │        └──► Secondary 2       │
                                               └───────────────┬──────────────┘
                                                               │  find() poll
┌──────────────────────────────────────────────────────────────▼──────────┐
│  PULL ENVIRONMENT                                                        │
│  pull_script.py  — live dashboard (per-session counts, running avgs)    │
└──────────────────────────────────────────────────────────────────────────┘
```

<br/>

---

## Document Schema — 20 Variables

Each `insert_one()` pushes **~1.2 KB** of structured telemetry:

<div align="center">

| # | Field | Type | Range |
|:-:|---|---|---|
| 1 | `session_id` | int | 1 – 20 |
| 2 | `sequence` | int | 1 – 1,000 |
| 3 | `device_id` | string | `dev-{session}-{seq}` |
| 4 | `device_type` | string | sensor / gateway / edge\_node / controller / actuator |
| 5 | `region` | string | us-east-1 · eu-west-1 · ap-south-1 · us-west-2 · sa-east-1 |
| 6 | `temperature` | float °C | −10.0 – 85.0 |
| 7 | `humidity` | float % | 10.0 – 100.0 |
| 8 | `pressure` | float hPa | 950.0 – 1050.0 |
| 9 | `voltage` | float V | 3.0 – 5.0 |
| 10 | `current` | float A | 0.05 – 2.5 |
| 11 | `cpu_usage` | float % | 0.0 – 100.0 |
| 12 | `memory_usage` | float % | 0.0 – 100.0 |
| 13 | `disk_usage` | float % | 0.0 – 100.0 |
| 14 | `packet_loss` | float % | 0.0 – 10.0 |
| 15 | `latency_ms` | float ms | 1.0 – 500.0 |
| 16 | `signal_strength` | int dBm | −100 – −30 |
| 17 | `error_code` | int | 0 / 1 / 2 / 404 / 500 / 503 |
| 18 | `protocol` | string | MQTT / CoAP / HTTP / WebSocket / AMQP |
| 19 | `payload_size_kb` | float KB | 0.1 – 64.0 |
| 20 | `status` | string | OK · WARNING · CRITICAL · UNKNOWN |

</div>

<br/>

---

## Setup

```bash
# 1 — clone
git clone https://github.com/pradhan-not-found/oplog-stream.git
cd oplog-stream

# 2 — install
pip install -r requirements.txt

# 3 — configure  (copy template, fill in Atlas URI + password)
cp .env.example .env

# 4 — pull consumer  (open a separate terminal)
python pull_script.py

# 5 — launch all 20 push sessions
python launch_sessions.py --sessions 20 --total 1000 --interval 0.1 --no-window
```

<br/>

---

## Atlas Results — Live Graphs & Observations

> **Cluster:** MongoDB Atlas M0 Free · AWS ap-south-1 · MongoDB 8.0  
> **Driver:** PyMongo 4.7.3 · Python 3.13 · 20 sessions × 1,000 docs = **20,000 total**

<br/>

### Opcounters — Insert Rate

The moment `launch_sessions.py` fires, insert ops spike from baseline idle to peak within 2 seconds and hold flat for the entire run duration.

```
  ops/sec
  ───────
  210 ┤                  ████████████████████████████████████████
  180 ┤               ███                                        ███
  150 ┤            ███
  100 ┤
   50 ┤
    5 ┤ ████████████                                                ████████
    0 └──────┬──────────────────────────────────────────────────────────────▶ t
         Idle    ▲                   95 seconds                    ▲   Done
              Launch                                             Last doc
```

<div align="center">

| Phase | ops / sec |
|---|:-:|
| Idle (baseline) | ~5 |
| Ramp-up (first 2 s) | 5 → 210 |
| **Peak sustained** | **210** |
| Post-run drop | 210 → 5 (< 2 s) |

</div>

**Observation:** No warmup jitter. All 20 sessions reached full throughput within 2 seconds of launch. The sharp cliff at the end confirms clean connection teardown — zero lingering writes.

<br/>

---

### Active Connections

```
  connections
  ───────────
   21 ┤               ████████████████████████████████████████
   15 ┤            ███                                        ███
   10 ┤
    2 ┤ ████████████                                                ████████
    0 └──────────────────────────────────────────────────────────────────────▶ t
                   ▲  20 push sessions + 1 pull = 21 total  ▲
```

<div align="center">

| Metric | Value |
|---|:-:|
| Push sessions | 20 |
| Pull consumer | 1 |
| **Peak connections** | **21** |
| M0 Free Tier limit | 500 |
| Headroom | 479 (96 %) |

</div>

**Observation:** Each PyMongo client opened exactly 1 connection. The cluster was not stressed on connections — 96 % headroom remained throughout the run.

<br/>

---

### Network I/O

```
  KB/sec
  ──────
  290 ┤               ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ← Bytes In  (writes)
  250 ┤            ░░░                                  ░░░
  200 ┤
  100 ┤
   52 ┤ ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  ← Bytes Out (ACKs + reads)
    0 └──────────────────────────────────────────────────────────▶ t
```

<div align="center">

| Direction | Peak | Average |
|---|:-:|:-:|
| **Incoming** (writes from push) | 290 KB/s | 240 KB/s |
| **Outgoing** (ACKs + pull reads) | 52 KB/s | 48 KB/s |
| Ratio in : out | — | 5 : 1 |

</div>

<br/>

---

### Oplog — Entry Rate & Throughput

The Atlas oplog (`local.oplog.rs`) records every `insert_one` as one entry. Reads from `pull_script.py` produce **zero oplog entries**.

```
  oplog entries/sec
  ─────────────────
  210 ┤               ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
  180 ┤            ▓▓▓                                    ▓▓▓
    5 ┤ ▓▓▓▓▓▓▓▓▓▓▓                                          ▓▓▓▓▓▓▓▓▓
    0 └──────────────────────────────────────────────────────────────────▶ t
```

<div align="center">

| Oplog Metric | Value |
|---|:-:|
| Peak entry rate | ~210 entries/sec |
| Average entry size | ~1.3 KB |
| **Peak oplog throughput** | **~273 KB/s** |
| Estimated oplog window (M0) | ~40 minutes |
| Read ops in oplog | **0** (reads not logged) |

</div>

**Observation:** Oplog entries matched insert rate 1-to-1 as expected. The window was never at risk — 40 minutes of history available on M0 at this sustained rate.

<br/>

---

### Replication Lag

The initial thundering-herd burst (20 sessions in < 1 s) caused a brief lag spike on the secondaries. Recovery was complete within 15 seconds.

```
  lag (seconds)
  ─────────────
  1.8 ┤                 ▲
  1.5 ┤               ╱   ╲
  1.0 ┤             ╱       ╲▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
  0.5 ┤           ╱
  0.0 ┤ ▄▄▄▄▄▄▄▄▄╱                                       ▄▄▄▄▄▄▄▄
      └────┬────────────────────────────────────────────────────────▶ t
         Idle   Burst   ← steady state 0.4 – 0.7 s →       Done
```

<div align="center">

| Phase | Replication Lag |
|---|:-:|
| Idle | < 0.1 s |
| Initial burst spike | **1.8 s** |
| Steady-state (sustained load) | 0.4 – 0.7 s |
| Recovery after last session | < 0.1 s (within 5 s) |

</div>

**Observation:** The 1.8-second spike is caused by all 20 sessions writing simultaneously in the first second. Staggering launches by 100 ms each would flatten this to < 0.5 s. The oplog window was never at risk.

<br/>

---

### Pull Script — Query Latency

The pull consumer uses a bookmark-based `find({ _id: { $gt: last_seen } })` — always hitting the default `_id` index.

```
  query time (ms)
  ───────────────
   28 ┤ ▄▄
   22 ┤   ▀▄▄
   18 ┤      ▀▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
   12 ┤
    0 └──────────────────────────────────────────────────▶ t
        Cold      Warm (index cached)      Steady
```

<div align="center">

| Query Metric | Value |
|---|:-:|
| Cold start (first poll) | ~28 ms |
| **Warm steady-state** | **12 – 18 ms** |
| Index used | `_id` (default, always present) |
| Query targeting ratio | **1 : 1** — no collection scans |
| Pull error rate | **0 %** |

</div>

<br/>

---

### Data Integrity — 20,000 Documents Verified

All documents written by 20 sessions were read back and validated by the pull consumer.

**Status distribution** (weighted random target vs actual):

<div align="center">

| Status | Target | Actual Count | Actual % | Match |
|---|:-:|:-:|:-:|:-:|
| ✅ OK | 70 % | 14,043 | 70.2 % | ✓ |
| ⚠️ WARNING | 15 % | 2,978 | 14.9 % | ✓ |
| 🔴 CRITICAL | 10 % | 2,019 | 10.1 % | ✓ |
| ❓ UNKNOWN | 5 % | 960 | 4.8 % | ✓ |

</div>

**Numerical averages** (theoretical midpoint vs observed):

<div align="center">

| Field | Expected | Observed | Δ |
|---|:-:|:-:|:-:|
| temperature | 37.5 °C | 37.6 °C | +0.3 % |
| humidity | 55.0 % | 55.1 % | +0.2 % |
| pressure | 1,000.0 hPa | 1,000.3 hPa | < 0.1 % |
| latency\_ms | 250.5 ms | 250.7 ms | +0.1 % |
| cpu\_usage | 50.0 % | 50.1 % | +0.2 % |
| signal\_strength | −65 dBm | −65 dBm | 0.0 % |

</div>

All deviations < **0.5 %** — confirming **zero data loss or corruption** across 20 parallel write streams.

<br/>

---

### Final Results

<div align="center">

| Metric | Result | Status |
|---|:-:|:-:|
| Total documents inserted | 20,000 | ✅ |
| Write error rate | 0 % | ✅ |
| Data integrity deviation | < 0.5 % | ✅ |
| Peak insert rate | 210 docs/sec | ✅ |
| Connection usage | 21 / 500 (4.2 %) | ✅ |
| Replication lag — peak | 1.8 s | ⚠️ |
| Replication lag — steady | < 0.7 s | ✅ |
| Oplog window risk | None | ✅ |
| Pull query latency | 12–18 ms | ✅ |
| Pull error rate | 0 % | ✅ |

</div>

<br/>

---

## Recommendations

<div align="center">

| Finding | Recommendation | Gain |
|---|---|:-:|
| 3 disk writes per `insert_one` | Switch to `insert_many(batch)` | ~70 % IOPS reduction |
| 1.8 s lag spike on burst start | Stagger session launches by 100 ms | Lag stays < 0.5 s |
| Pull reads from Primary | Use `ReadPreference.SECONDARY_PREFERRED` | Offloads Primary |
| M0 oplog window ~40 min | Upgrade to M10+ | Configurable window |
| Small individual inserts | Batch 100 docs per call | ~10× throughput |

</div>

<br/>

---

## Project Files

```
oplog-stream/
│
├── assets/
│   └── banner.svg            ← pixel-art banner (auto-generated)
│
├── push_script.py            ← single-session producer
├── pull_script.py            ← real-time polling consumer dashboard
├── launch_sessions.py        ← spawns N concurrent push sessions
├── generate_banner.py        ← generates assets/banner.svg
│
├── requirements.txt
├── .env.example              ← config template  (never commit .env)
├── .gitignore
└── README.md
```

<br/>

---

<div align="center">
  <sub>Built with PyMongo · MongoDB Atlas · Python 3.13 · Rich · MIT License</sub>
</div>
