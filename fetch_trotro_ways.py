import requests
import psycopg2
import time

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "5432",
    "dbname": "informal_transport",
    "user": "transit_admin",
    "password": "ghana_transit_2024"
}

# Our exact bounding box: South, West, North, East
BBOX = "5.4545,-0.59,5.92,0.095"

# Headers required by Overpass to prevent 406 errors
HEADERS = {
    "User-Agent": "AccraTransportEngine/1.0 (ddelaraiye@github.com)" # Put your real email here
}

def get_trotro_way_ids():
    """Queries Overpass API for all ways that are part of a bus/minibus route in Accra."""
    
    # Using kumi.systems - often more stable for heavy queries than the main overpass-api.de
    overpass_url = "https://overpass.kumi.systems/api/interpreter"
    
    # Optimized query: only get relations, then recurse down to get the way IDs they contain
    query = f"""
    [out:json][timeout:120];
    (
      relation["route"~"bus|minibus|share_taxi"]({BBOX});
    );
    out tags;
    >;
    out ids qt;
    """
    
    print("[API] Fetching tro-tro route ways from Overpass API (this may take 30-60s)...")
    response = requests.post(overpass_url, data={'data': query}, headers=HEADERS)
    
    # Check for HTTP errors and print the actual Overpass error message if it fails
    if response.status_code != 200:
        print(f"[API] Error {response.status_code}: {response.text}")
        raise Exception("Overpass API rejected the request.")
        
    data = response.json()
    
    # Parse the results to get only unique Way IDs
    way_ids = set()
    for element in data.get('elements', []):
        if element.get('type') == 'way':
            way_ids.add(element['id'])
            
    print(f"[API] Found {len(way_ids)} unique road segments mapped as tro-tro routes.")
    return list(way_ids)

def update_database(way_ids):
    """Adds a column to our edges table and flags the tro-tro ways."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 1. Add a boolean column if it doesn't exist
    print("[DB] Adding 'is_trotro_route' flag to edges table...")
    cur.execute("ALTER TABLE routing_network.edges ADD COLUMN IF NOT EXISTS is_trotro_route BOOLEAN DEFAULT FALSE;")
    
    # 2. Flag the ways that came from the API by matching them against the raw OSM line table
    print(f"[DB] Matching and flagging {len(way_ids)} edges (this might take a few seconds)...")
    
    update_query = """
        UPDATE routing_network.edges e
        SET is_trotro_route = TRUE
        FROM planet_osm_line p
        WHERE p.osm_id = ANY(%s) AND ST_Equals(e.geom, p.way);
    """
        
    cur.execute(update_query, (way_ids,))
    affected_rows = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"[DB] ✅ Success! {affected_rows} edges in your routing graph are now flagged as official tro-tro corridors.")

if __name__ == "__main__":
    try:
        ways = get_trotro_way_ids()
        if ways:
            update_database(ways)
        else:
            print("[API] No tro-tro routes found in this bounding box.")
    except Exception as e:
        print(f"[SYSTEM] Failed: {e}")