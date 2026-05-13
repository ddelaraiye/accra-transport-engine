import argparse
import psycopg2

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "5432",
    "dbname": "informal_transport",
    "user": "transit_admin",
    "password": "ghana_transit_2024"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def resolve_base_node(cursor, location_text):
    """
    Translates human text to a transit base ID.
    1. Finds the closest OSM bus stop matching the text.
    2. Finds the closest 400m macro-base to that bus stop.
    """
    query = """
        SELECT b.base_id, b.base_name 
        FROM routing_network.transit_bases b
        ORDER BY b.geom <-> (
            SELECT way FROM planet_osm_point 
            WHERE highway = 'bus_stop' AND name ILIKE %s 
            LIMIT 1
        ) 
        LIMIT 1;
    """
    cursor.execute(query, (f"%{location_text}%",))
    result = cursor.fetchone()
    
    if not result:
        raise ValueError(f"Could not find a transit base near '{location_text}'. Try a major landmark or station.")
    return result[0], result[1]

def calculate_macro_route(cursor, start_id, end_id):
    """
    Routes using the 240-base macro graph.
    """
    query = """
        WITH path AS (
            -- MUST select 'edge' to calculate time, 'seq' to order steps, 'node' for names
            SELECT seq, edge, node FROM pgr_dijkstra(
                'SELECT id, source_base AS source, target_base AS target, total_time_mins AS cost FROM routing_network.base_connections',
                %s, %s
            )
        )
        SELECT 
            -- Calculate total time by summing the costs of the edges traversed
            (SELECT ROUND(SUM(total_time_mins)::numeric, 2) 
             FROM routing_network.base_connections 
             WHERE id IN (SELECT edge FROM path WHERE edge != -1)) as total_time,
            -- Get the sequence of base names
            array_agg(b.base_name ORDER BY p.seq) as steps
        FROM path p
        JOIN routing_network.transit_bases b ON p.node = b.base_id;
    """
    cursor.execute(query, (start_id, end_id))
    result = cursor.fetchone()
    
    if not result or result[0] is None:
        raise ValueError("No tro-tro route found between these macro-bases.")
        
    return result[0], result[1]

def main():
    parser = argparse.ArgumentParser(description="Accra Informal Transport Decision Engine (Macro Routing)")
    parser.add_argument("--from", dest="start", required=True, help="Start location (e.g., 'Kaneshie')")
    parser.add_argument("--to", dest="end", required=True, help="Destination (e.g., 'Madina')")
    
    args = parser.parse_args()

    print(f"\n[ENGINE] Calculating macro-route from {args.start} to {args.end}...")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 1. Resolve bases
                start_id, start_db_name = resolve_base_node(cur, args.start)
                end_id, end_db_name = resolve_base_node(cur, args.end)
                
                # 2. Calculate Route
                time_mins, steps = calculate_macro_route(cur, start_id, end_id)
                
                # 3. Format Output as Human Intelligence
                clean_steps = []
                seen = set()
                for step in steps:
                    if step and step not in seen and not step.replace(" ", "").isdigit():
                        if step.lower() not in ['fidelity', 'none', 'cal bank', 'stanbic']:
                            clean_steps.append(step)
                            seen.add(step)

                # Calculate heuristic fare (Minimum fare in Accra is GHS 3.00)
                fare_min = max(3, int(time_mins / 3))
                fare_max = fare_min + 2

                # Generate the narrative string (Use user's words for start/end)
                if len(clean_steps) <= 2:
                    narrative = f"Take a direct trotro from {args.start.capitalize()} to {args.end.capitalize()}."
                else:
                    middle_hubs = ", ".join(clean_steps[1:-1])
                    narrative = f"From {args.start.capitalize()}, take a trotro through {middle_hubs}, and alight at {args.end.capitalize()}."
                # Print the Decision Intelligence
                print("\n" + "="*50)
                print("🧠 INFORMAL TRANSIT DECISION")
                print("="*50)
                print(f"Route: {args.start.capitalize()} -> {args.end.capitalize()}")
                print(f"Time:  ~{time_mins} minutes")
                print(f"Fare:  GHS {fare_min}.00 - {fare_max}.00 (Estimated)")
                print("-" * 50)
                print("INSTRUCTION:")
                print(f"  {narrative}")
                print("="*50 + "\n")

    except Exception as e:
        print(f"\n❌ ENGINE ERROR: {e}\n")

if __name__ == "__main__":
    main()