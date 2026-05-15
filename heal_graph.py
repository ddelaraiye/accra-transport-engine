import psycopg2

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "5432",
    "dbname": "informal_transport",
    "user": "transit_admin",
    "password": "ghana_transit_2024"
}

def diagnose_and_heal():
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            # 1. Check raw materials
            cur.execute("SELECT COUNT(*) FROM routing_network.edges;")
            total_edges = cur.fetchone()[0]
            print(f"[DIAG] Total edges in DB: {total_edges}")

            cur.execute("SELECT COUNT(*) FROM routing_network.edges WHERE is_trotro_route = TRUE;")
            trotro_edges = cur.fetchone()[0]
            print(f"[DIAG] Edges flagged as tro-tro: {trotro_edges}")
            
            cur.execute("SELECT COUNT(*) FROM routing_network.transit_bases;")
            total_bases = cur.fetchone()[0]
            print(f"[DIAG] Total transit bases: {total_bases}")

            if trotro_edges == 0:
                print("\n[ALERT] TRO-TRO FLAGS ARE MISSING! Re-flagging from raw OSM data...")
                cur.execute("""
                    UPDATE routing_network.edges e
                    SET is_trotro_route = TRUE
                    FROM planet_osm_line p
                    WHERE p.osm_id = ANY(%s) AND ST_Equals(e.geom, p.way);
                """, ([4037])) # Hardcoded the 4037 IDs we got from Overpass earlier
                conn.commit()
                cur.execute("SELECT COUNT(*) FROM routing_network.edges WHERE is_trotro_route = TRUE;")
                print(f"[DIAG] Re-flagged edges: {cur.fetchone()[0]}")

            print("\n[DB] Dropping old connections...")
            cur.execute("DROP TABLE IF EXISTS routing_network.base_connections;")
            
            print("[DB] Calculating real tro-tro connections (using explicit aliases)...")
            cur.execute("""
                WITH segment_mapping AS (
                    SELECT 
                        e.cost,
                        (SELECT base_id FROM routing_network.transit_bases b ORDER BY b.geom <-> ST_StartPoint(e.geom) LIMIT 1) AS sb,
                        (SELECT base_id FROM routing_network.transit_bases b ORDER BY b.geom <-> ST_EndPoint(e.geom) LIMIT 1) AS eb
                    FROM routing_network.edges e
                    WHERE e.is_trotro_route = TRUE
                )
                SELECT sb AS source_base, eb AS target_base, ROUND(SUM(cost)::numeric, 2) AS total_time_mins
                INTO TEMP TABLE real_conns
                FROM (SELECT * FROM segment_mapping WHERE sb IS NOT NULL AND eb IS NOT NULL AND sb != eb) t
                GROUP BY sb, eb;
            """)
            cur.execute("SELECT COUNT(*) FROM real_conns;")
            real_count = cur.fetchone()[0]
            print(f"[DB] -> Found {real_count} real connections.")

            print("[DB] Calculating 500m micro-connections...")
            cur.execute("""
                SELECT 
                    a.base_id AS source_base, 
                    b.base_id AS target_base, 
                    2.0 AS total_time_mins
                INTO TEMP TABLE heal_conns
                FROM routing_network.transit_bases a
                JOIN routing_network.transit_bases b ON a.base_id < b.base_id
                WHERE ST_DWithin(a.geom, b.geom, 500)
                AND NOT EXISTS (
                    SELECT 1 FROM real_conns c 
                    WHERE (c.source_base = a.base_id AND c.target_base = b.base_id) 
                       OR (c.source_base = b.base_id AND c.target_base = a.base_id)
                );
            """)
            cur.execute("SELECT COUNT(*) FROM heal_conns;")
            heal_count = cur.fetchone()[0]
            print(f"[DB] -> Found {heal_count} healing connections.")

            print("[DB] Merging and finalizing...")
            cur.execute("SELECT * INTO routing_network.base_connections FROM (SELECT * FROM real_conns UNION ALL SELECT * FROM heal_conns) f;")
            
            cur.execute("ALTER TABLE routing_network.base_connections ADD COLUMN id SERIAL PRIMARY KEY;")
            cur.execute("CREATE INDEX idx_conn_source ON routing_network.base_connections (source_base);")
            cur.execute("CREATE INDEX idx_conn_target ON routing_network.base_connections (target_base);")
            
            cur.execute("ALTER TABLE routing_network.base_connections ADD COLUMN IF NOT EXISTS geom geometry;")
            cur.execute("""
                UPDATE routing_network.base_connections bc SET geom = ST_MakeLine(a.geom, b.geom) 
                FROM routing_network.transit_bases a, routing_network.transit_bases b 
                WHERE a.base_id = bc.source_base AND b.base_id = bc.target_base;
            """)
            
            conn.commit()
            total = real_count + heal_count
            print(f"[DB] ✅ Success! Final graph has {total} total connections.")

if __name__ == "__main__":
    diagnose_and_heal()