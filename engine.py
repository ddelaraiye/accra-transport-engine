import argparse
import psycopg2
from psycopg2 import sql

# Database connection details
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "5432",
    "dbname": "informal_transport",
    "user": "transit_admin",
    "password": "ghana_transit_2024"
}

def get_db_connection():
    """Connect to the Accra Transport PostGIS database."""
    return psycopg2.connect(**DB_CONFIG)

def find_valid_node(cursor, location_name):
    """
    Finds a routable node near a given location name.
    1. Queries OSM data for the GPS coordinate of the bus stop.
    2. Finds the closest node in our routing graph that is an actual 
       intersection (not a dead-end).
    """
    query = """
        WITH target AS (
            SELECT way FROM planet_osm_point 
            WHERE name ILIKE %s AND highway = 'bus_stop' 
            LIMIT 1
        ),
        valid_nodes AS (
            -- Filter for nodes that have roads both leaving and arriving (intersections)
            SELECT v.id, v.geom
            FROM routing_network.vertices v
            WHERE EXISTS (SELECT 1 FROM routing_network.edges e WHERE e.source = v.id)
              AND EXISTS (SELECT 1 FROM routing_network.edges e WHERE e.target = v.id)
            UNION
            SELECT v.id, v.geom
            FROM routing_network.vertices v
            JOIN routing_network.edges e1 ON v.id = e1.source
            JOIN routing_network.edges e2 ON v.id = e2.target
            WHERE e1.id != e2.id
        )
        SELECT v.id FROM valid_nodes v, target t
        ORDER BY v.geom <-> t.way LIMIT 1;
    """
    # Add wildcards so "Circle" matches "Circle Station"
    cursor.execute(query, (f"%{location_name}%",))
    result = cursor.fetchone()
    
    if not result:
        raise ValueError(f"Could not find a valid routing node for '{location_name}'. Check the spelling.")
    return result[0]

def calculate_route(cursor, start_node, end_node):
    """
    Runs pgRouting Dijkstra between two nodes.
    Returns total time in minutes and the distinct street names used.
    """
    query = """
        WITH path AS (
            SELECT edge FROM pgr_dijkstra(
                'SELECT id, source, target, cost FROM routing_network.edges',
                %s, %s
            ) WHERE edge != -1
        )
        SELECT 
            ROUND(SUM(e.cost)::numeric, 2) as total_time,
            array_agg(DISTINCT NULLIF(e.route_name, '')) as roads_used
        FROM path p 
        JOIN routing_network.edges e ON p.edge = e.id;
    """
    cursor.execute(query, (start_node, end_node))
    result = cursor.fetchone()
    
    if not result or result[0] is None:
        raise ValueError("No drivable path found between these locations.")
        
    return result[0], result[1]

def main():
    parser = argparse.ArgumentParser(description="Accra Informal Transport Decision Engine")
    parser.add_argument("--from", dest="start", required=True, help="Start location (e.g., 'Circle')")
    parser.add_argument("--to", dest="end", required=True, help="Destination (e.g., 'Madina')")
    
    args = parser.parse_args()

    print(f"\n[ENGINE] Calculating route from {args.start} to {args.end}...")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 1. Find safe start and end nodes
                start_id = find_valid_node(cur, args.start)
                end_id = find_valid_node(cur, args.end)
                
                # 2. Calculate the route
                time_mins, roads = calculate_route(cur, start_id, end_id)
                
                # 3. Format output for human reading
                # Filter out None values from the roads array
                clean_roads = [str(r) for r in roads if r is not None]
                road_summary = ", ".join(clean_roads[:3]) # Show top 3 road names
                
                print("\n" + "="*50)
                print("✅ ROUTE FOUND")
                print("="*50)
                print(f"From:    {args.start.capitalize()}")
                print(f"To:      {args.end.capitalize()}")
                print(f"Time:    ~{time_mins} minutes")
                print(f"Via:     {road_summary if road_summary else 'Local street network'}")
                print("="*50 + "\n")

    except Exception as e:
        print(f"\n❌ ROUTING ERROR: {e}\n")

if __name__ == "__main__":
    main()