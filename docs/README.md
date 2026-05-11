# **Accra Informal Transport Decision Engine**

A spatially-aware routing engine built to calculate optimal paths across the informal tro-tro network of Greater Accra.



### Architecture

Instead of flat files, this system utilizes a spatial database pipeline:



Data Source: OpenStreetMap (OSM)

Storage \& Math: PostgreSQL + PostGIS + pgRouting (Dockerized)

Logic: Python CLI (Dead-end bypass, topology traversal)

Visualization: QGIS

Prerequisites

Docker Desktop (Running)

Python 3.x

pip install psycopg2-binary

Quick Start

1\. Start the Database Engine:



docker compose up -d

2\. Run a Route Query:



bash



python engine.py --from "Circle" --to "Madina"

Example Output

text



==================================================

✅ ROUTE FOUND

==================================================

From:    Circle

To:      Madina

Time:    \~35.00 minutes

Via:     37 Circle, Barnes Avenue, Castle Road

==================================================

### Project Structure

docker-compose.yml: Spins up the PostGIS/pgRouting container.

data/: Contains the OSM extract (ignored from Git).

scripts/: SQL topology builders.

engine.py: Python wrapper for human-readable routing.

docs/: Build logs and methodology documentation.

### Methodology Note

The current routing algorithm uses Dijkstra's shortest path based on physical road lengths (assuming 40 km/h). Future iterations will introduce weighting based on known informal transit corridors (e.g., prioritizing the N1 Highway over residential shortcuts) by integrating OSM Route Relations.

