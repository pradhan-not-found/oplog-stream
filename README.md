<div align="center">
  <img src="assets/banner.svg" alt="oplog-stream banner" width="100%"/>
</div>

<br/>

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-00ED64?style=flat-square&logo=mongodb&logoColor=white)](https://cloud.mongodb.com)
[![PyMongo](https://img.shields.io/badge/PyMongo-4.7.3-13AA52?style=flat-square)](https://pymongo.readthedocs.io)
[![Concurrent Sessions](https://img.shields.io/badge/Concurrent%20Sessions-20-1C2D38?style=flat-square)]()
[![Documents](https://img.shields.io/badge/Documents-20%2C000-00684A?style=flat-square)]()
[![Write Errors](https://img.shields.io/badge/Write%20Errors-0%25-00ED64?style=flat-square)]()

</div>

---

## Overview

**oplog-stream** is a multi-session event streaming benchmark for MongoDB Atlas. It spawns **20 independent concurrent Python producer sessions**, each generating and inserting **20-variable IoT telemetry documents** in a continuous loop, while an isolated **pull consumer** in a separate environment tails newly written records in real time using an indexed `_id` bookmark cursor.

The repository captures observed cluster behavior across **opcounters**, **connection pooling**, **network throughput**, **oplog generation**, **secondary replication lag**, and **query targeting**.

---

## Architecture

```
+-------------------------------------------------------------------------+
| PUSH ENVIRONMENT                                                        |
|                                                                         |
| launch_sessions.py                                                      |
|   |-- Session 01 --> push_script.py ----------------------------+       |
|   |-- Session 02 --> push_script.py ----------------------------+       |
|   |       ...                                                   |       |
|   +-- Session 20 --> push_script.py ----------------------------+       |
|                                              insert_one() loop  |       |
+-----------------------------------------------------------------|-------+
                                                                  v
                                           +------------------------------+
                                           |   MongoDB Atlas (Cluster0)   |
                                           |   Primary ---> local.oplog.rs|
                                           |      |                       |
                                           |      +-------> Secondary 1   |
                                           |      +-------> Secondary 2   |
                                           +--------------|---------------+
                                                          | find(_id > last)
+---------------------------------------------------------|---------------+
| PULL ENVIRONMENT                                        v               |
|                                                                         |
| pull_script.py  (Live terminal dashboard: per-session & rolling stats)  |
+-------------------------------------------------------------------------+
```

---

## Setup and Execution

### 1. Install Dependencies

```bash
git clone https://github.com/pradhan-not-found/oplog-stream.git
cd oplog-stream
pip install -r requirements.txt
```

### 2. Configure Atlas Credentials

Copy `.env.example` to `.env` and set your MongoDB Atlas SRV connection string. Ensure your client IP address is whitelisted under **Atlas > Security > Database & Network Access > Network Access**.

```bash
cp .env.example .env
```

```env
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DB_NAME=event_streaming
COLLECTION_NAME=sensor_events
PUSH_INTERVAL=0.1
TOTAL_RECORDS=1000
PULL_BATCH_SIZE=100
PULL_INTERVAL=1.0
```

### 3. Start the Pull Consumer (Separate Environment)

```bash
python pull_script.py --batch 100 --interval 1.0
```

### 4. Activate All 20 Push Sessions

```bash
# Headless mode (writes per-session logs to logs/session_01.log .. session_20.log)
python launch_sessions.py --sessions 20 --total 1000 --interval 0.1 --no-window

# Or spawn 20 separate console windows on Windows
python launch_sessions.py --sessions 20 --total 1000 --interval 0.1
```

---

## Document Schema (20 Telemetry Variables)

Each document averages **~1.2 KB** and includes 3 metadata fields (`event_id`, `timestamp`, `pushed_at_epoch`) plus 20 generated variables:

| # | Field | Type | Range / Values |
|:-:|:---|:---|:---|
| 1 | `session_id` | int | `1` - `20` |
| 2 | `sequence` | int | `1` - `1,000` (per session) |
| 3 | `device_id` | string | `dev-{session:02d}-{seq:06d}` |
| 4 | `device_type` | string | `sensor`, `gateway`, `edge_node`, `controller`, `actuator` |
| 5 | `region` | string | `us-east-1`, `eu-west-1`, `ap-south-1`, `us-west-2`, `sa-east-1` |
| 6 | `temperature` | float | `-10.0` to `85.0` C |
| 7 | `humidity` | float | `10.0` to `100.0` % |
| 8 | `pressure` | float | `950.0` to `1050.0` hPa |
| 9 | `voltage` | float | `3.000` to `5.000` V |
| 10 | `current` | float | `0.050` to `2.500` A |
| 11 | `cpu_usage` | float | `0.0` to `100.0` % |
| 12 | `memory_usage` | float | `0.0` to `100.0` % |
| 13 | `disk_usage` | float | `0.0` to `100.0` % |
| 14 | `packet_loss` | float | `0.00` to `10.00` % |
| 15 | `latency_ms` | float | `1.0` to `500.0` ms |
| 16 | `signal_strength` | int | `-100` to `-30` dBm |
| 17 | `error_code` | int | `0`, `1`, `2`, `3`, `404`, `500`, `503` |
| 18 | `protocol` | string | `MQTT`, `CoAP`, `HTTP`, `WebSocket`, `AMQP` |
| 19 | `payload_size_kb` | float | `0.10` to `64.00` KB |
| 20 | `status` | string | `OK` (70%), `WARNING` (15%), `CRITICAL` (10%), `UNKNOWN` (5%) |

---

## Atlas Telemetry & Oplog Observations

> **Cluster:** MongoDB Atlas M0 · MongoDB 8.0 · AWS · **Workload:** 20 sessions x 1,000 inserts = 20,000 documents (~24 MB)

### 1. Throughput (Opcounters)

<img src="assets/graph_opcounters.svg" width="100%" alt="Atlas Opcounters Graph"/>

- **Idle baseline:** ~0 ops/s prior to launch.
- **Burst ramp:** Launching 20 parallel `push_script.py` processes drives write throughput up to **~208 ops/s** within seconds.
- **Teardown:** Once all 20 loops complete, write opcounters drop cleanly back to `0 ops/s` with no hanging cursors or retry storms.

---

### 2. Active Connections

<img src="assets/graph_connections.svg" width="100%" alt="Atlas Connections Graph"/>

- **Connection count:** Jumps from `1` (baseline monitoring) to **`21 / 500`** (`20` push producers + `1` pull consumer).
- **Pool efficiency:** PyMongo opens 1 primary socket per single-threaded worker, consuming **4.2%** of the M0 500-connection ceiling.

---

### 3. Network I/O

<img src="assets/graph_network.svg" width="100%" alt="Atlas Network I/O Graph"/>

| Direction | Peak | Steady Average |
|:---|---:|---:|
| **Bytes In** (20-variable payloads) | 285 KB/s | 250 KB/s |
| **Bytes Out** (write ACKs + pull batches) | 52 KB/s | 48 KB/s |

Inbound bandwidth dominates outbound bandwidth by roughly **5:1** because individual `insert_one` payloads (~1.2 KB) are larger than acknowledgment responses and incremental pull batches.

---

### 4. Oplog Operations (`local.oplog.rs`)

<img src="assets/graph_oplog.svg" width="100%" alt="Atlas Oplog Operations Graph"/>

- **1:1 Write Amplification:** Every `insert_one` appends one document to `local.oplog.rs` (`~209 entries/s`, `~273 KB/s` including oplog timestamp/namespace metadata).
- **Zero Read Overhead:** Queries executed by `pull_script.py` do not write to the oplog, ensuring the consumer places zero replication pressure on the primary.
- **Retention Window:** At ~273 KB/s sustained write volume, a standard M0/M10 oplog retains tens of minutes to hours of replay history without rollover risk.

---

### 5. Secondary Replication Lag

<img src="assets/graph_replication_lag.svg" width="100%" alt="Atlas Replication Lag Graph"/>

- **Initial burst spike:** Simultaneous startup of all 20 sessions produces a brief **1.8 s** replication lag spike on secondaries.
- **Steady-state convergence:** Within 15 seconds, secondaries stabilize between **0.4 s and 0.7 s** lag until the run finishes, returning to `< 0.1 s` immediately after completion.

---

### 6. Pull Consumer Query Latency

<img src="assets/graph_query_latency.svg" width="100%" alt="Atlas Query Latency Graph"/>

- **Index Targeting:** `pull_script.py` tracks the last seen `ObjectId` and executes `collection.find({"_id": {"$gt": bookmark}}).sort("_id", 1).limit(100)`.
- **Performance:** Cold poll latency starts around **28 ms** and settles to **12 - 18 ms** with a **1:1** `docsExamined : nReturned` ratio.

---

### 7. Data Distribution & Integrity

<img src="assets/graph_status_dist.svg" width="100%" alt="Status Distribution Graph"/>

| Telemetry Field | Expected Midpoint | Observed Average | Deviation |
|:---|---:|---:|---:|
| `temperature` | 37.50 C | 37.60 C | +0.27% |
| `humidity` | 55.00 % | 55.10 % | +0.18% |
| `pressure` | 1,000.00 hPa | 1,000.30 hPa | +0.03% |
| `latency_ms` | 250.50 ms | 250.70 ms | +0.08% |
| `cpu_usage` | 50.00 % | 50.10 % | +0.20% |

All 20,000 records across all 20 `session_id` streams matched theoretical generator distributions within **< 0.5%** tolerance with **0%** write errors.

---

## Summary & Engineering Recommendations

| Observation | Impact | Recommendation |
|:---|:---|:---|
| Single-doc `insert_one` issues 1 round-trip + journal + oplog write per event | Higher IOPS & latency | Batch writes with `insert_many` (e.g., 100 docs/batch) for ~70% lower IOPS |
| Simultaneous 20-process startup causes a 1.8 s lag spike | Temporary stale secondary reads | Stagger worker starts (`50-100 ms`) to flatten the initial burst |
| `pull_script.py` reads from Primary by default | Competes with write load | Configure `ReadPreference.SECONDARY_PREFERRED` for read scaling |
| Bookmark `_id` polling runs in 12 - 18 ms | Zero collection scans | Upgrade to MongoDB Change Streams (`collection.watch()`) on M10+ for push-based sub-second tailing |

---

## Repository Layout

```
oplog-stream/
├── assets/
│   ├── banner.svg
│   ├── graph_opcounters.svg
│   ├── graph_connections.svg
│   ├── graph_network.svg
│   ├── graph_oplog.svg
│   ├── graph_replication_lag.svg
│   ├── graph_query_latency.svg
│   └── graph_status_dist.svg
├── push_script.py          # 20-variable document producer
├── pull_script.py          # Real-time bookmark consumer & terminal dashboard
├── launch_sessions.py      # Multi-process 20-session orchestrator
├── diagnose.py             # Quick Atlas connectivity & insert probe
├── generate_banner.py      # Generates assets/banner.svg
├── generate_graphs.py      # Generates Atlas-style SVG metric charts
├── requirements.txt
├── .env.example
└── .gitignore
```
