import psycopg2

from db import db_config

DB_CONFIG = db_config()

def find_base(intent_name, stop_name):
    query = "SELECT base_name, route_convergence_score FROM routing_network.transit_bases ORDER BY geom <-> (SELECT way FROM planet_osm_point WHERE name = %s LIMIT 1) LIMIT 1"
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (stop_name,))
            row = cur.fetchone()
            if row:
                print(f"Intent: {intent_name} | System Name: {row[0]} | Score: {row[1]}")
            else:
                print(f"Intent: {intent_name} | ERROR: Not found")

print("Finding mapped bases...")
find_base("Kaneshie", "Kaneshie Foot Bridge")
find_base("Madina", "Madina Zongo Junction")