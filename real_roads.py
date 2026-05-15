import psycopg2

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "5432",
    "dbname": "informal_transport",
    "user": "transit_admin",
    "password": "ghana_transit_2024"
}

def update_geometries():
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            print("[DB] Updating connections to use actual road geometries...")
            
            # For each connection, replace the straight line with the actual stitched roads
            cur.execute("""
                UPDATE routing_network.base_connections bc
                SET geom = sub.real_geom
                FROM (
                    SELECT 
                        bc.id,
                        ST_Union(e.geom) AS real_geom
                    FROM routing_network.base_connections bc
                    JOIN routing_network.edges e ON e.is_trotro_route = TRUE
                    WHERE ST_DWithin(e.geom, (SELECT geom FROM routing_network.transit_bases WHERE base_id = bc.source_base), 500)
                      AND ST_DWithin(e.geom, (SELECT geom FROM routing_network.transit_bases WHERE base_id = bc.target_base), 500)
                    GROUP BY bc.id
                ) sub
                WHERE bc.id = sub.id;
            """)
            
            updated = cur.rowcount
            conn.commit()
            print(f"[DB] ✅ Success! Updated {updated} connections to real road geometries.")

if __name__ == "__main__":
    update_geometries()