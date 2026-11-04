# Accra Informal Transport Decision Engine

A spatially-aware routing engine that calculates optimal paths across the informal **tro-tro** (minibus) network of Greater Accra, Ghana.

Instead of treating tro-tro travel as a black box, this project builds a real routing graph from OpenStreetMap data, clusters it into macro-level transit bases (stations/junctions), and answers the question riders actually ask:

> *"How do I get from Circle to Madina — which trotro do I take, where do I transfer, how long will it take, and what will it cost?"*

---

## Architecture

The system is built on a spatial database pipeline rather than flat files:

```
OpenStreetMap (Overpass API / osm2pgsql)
        │
        ▼
PostgreSQL + PostGIS + pgRouting   (Dockerized)
        │  • routing_network.edges / vertices   (raw road graph)
        │  • routing_network.transit_bases      (240 macro-bases, ~400m clusters)
        │  • routing_network.base_connections   (weighted, time-based edges)
        ▼
Python CLI Decision Engine (engine.py)
        │  • fuzzy base resolution (nearest bus stop → nearest macro-base)
        │  • Dijkstra shortest path over the macro graph
        │  • human-readable route narrative + fare heuristic
        ▼
QGIS Visualization (neon styling, Draw Effects, tiered labels)
```

| Layer | Technology |
|---|---|
| Data source | OpenStreetMap via Overpass API |
| Storage & math | PostgreSQL + PostGIS + pgRouting (Docker) |
| Logic | Python CLI (topology traversal, dead-end bypass) |
| Visualization | QGIS |

---

## Repository Layout

```
.
├── docker-compose.yml          # pgrouting/pgrouting image + PostGIS volume
├── engine.py                   # Main CLI decision engine (macro routing)
├── fetch_trotro_ways.py        # Pulls tro-tro route ways from Overpass API (Accra BBox)
├── find_bases.py               # Maps human intent names ("Kaneshie") to system base names
├── heal_graph.py               # Diagnostics & self-repair for missing tro-tro edge flags
├── real_roads.py               # Replaces straight-line connections with stitched road geometries
├── scripts/
│   ├── init_db.sql             # Enables PostGIS/pgRouting, creates routing_network schema
│   └── build_routing_graph.sql # Populates edges/vertices, builds topology
└── docs/README.md              # Original design notes
```

---

## Prerequisites

- **Docker Desktop** (running)
- **Python 3.x**
- Database dependencies installed locally:

```bash
pip install psycopg2-binary requests
```

---

## Quick Start

### 1. Start the database engine

```bash
docker compose up -d
```

This boots the `accra_transit_db` container (PostgreSQL + PostGIS + pgRouting) on port `5432` and runs `scripts/init_db.sql` automatically on first start.

### 2. Load OSM data

Import Greater Accra OSM data (e.g. via `osm2pgsql`) so the `planet_osm_line` / `planet_osm_point` tables exist, then build the routing graph:

```bash
psql -h 127.0.0.1 -U transit_admin -d informal_transport -f scripts/build_routing_graph.sql
```

Populate tro-tro specific route data and repair the graph as needed:

```bash
python fetch_trotro_ways.py   # fetch tro-tro route ways from Overpass API
python heal_graph.py          # diagnose & re-flag tro-tro edges, check bases
python real_roads.py          # snap connection geometries to actual roads
```

### 3. Run a route query

```bash
python engine.py --from "Circle" --to "Madina"
```

### Example Output

```
==================================================
🧠 INFORMAL TRANSIT DECISION
==================================================
Route: Circle -> Madina
Time:  ~34 minutes
Fare:  GHS 11.00 - 13.00 (Estimated)
--------------------------------------------------
INSTRUCTION:
  From Circle, take a trotro through Adabraka, 37 Estates,
  and alight at Madina.
==================================================
```

---

## How It Works

1. **Base resolution** — Your free-text location is matched to the closest OSM bus stop, then snapped to the nearest 400 m *macro-base* in `routing_network.transit_bases`.
2. **Macro routing** — `pgr_dijkstra` finds the lowest-cost path (cost = travel time in minutes) over `routing_network.base_connections`.
3. **Narrative generation** — Intermediate hubs are de-duplicated and assembled into plain-language boarding/alighting instructions.
4. **Fare heuristic** — Estimated using the Accra minimum fare (GHS 3.00) scaled by trip duration.

---

## Configuration

Credentials are **never hardcoded**. All scripts read them via `db.py` from environment variables, and `docker-compose.yml` reads the same variables from a `.env` file at the project root:

```bash
cp .env.example .env   # then set your own POSTGRES_PASSWORD
```

| Variable | Default | Description |
|---|---|---|
| `PGHOST` | `127.0.0.1` | Database host |
| `PGPORT` | `5432` | Database port (compose binds to `127.0.0.1` only) |
| `POSTGRES_DB` | `informal_transport` | Database name |
| `POSTGRES_USER` | `transit_admin` | Database user |
| `POSTGRES_PASSWORD` | *(required)* | No default — compose and `db.py` fail fast if unset |

> ⚠️ **Security note:** an earlier version of this repository shipped a plaintext password in every script and `docker-compose.yml`. That credential is now considered compromised — if it was ever used outside a disposable local database, rotate it there too. The port is also bound to loopback only; do not expose 5432 publicly unless deliberately required and secured.

---

## Troubleshooting

- **"Could not find a transit base near ..."** — Use a major landmark or station name; the fuzzy match relies on named OSM bus stops.
- **"No tro-tro route found between these macro-bases"** — The graph may be missing tro-tro flags; run `python heal_graph.py`.
- **Overpass API errors (406/timeouts)** — `fetch_trotro_ways.py` uses the `kumi.systems` mirror and sets a `User-Agent`; retry if the server is busy.

---

## Visualization

Load the `routing_network` tables into QGIS from the PostGIS layer. The final visualization uses Draw Effects and tiered labels with a neon styling scheme for the tro-tro corridors.

---

*Built for the informal transit networks of Accra — where the map doesn't end when the official routes do.*
