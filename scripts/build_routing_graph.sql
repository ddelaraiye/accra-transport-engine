-- 1. Clean existing tables
TRUNCATE TABLE routing_network.edges;
TRUNCATE TABLE routing_network.vertices;

-- 2. Populate Edges (The Roads)
-- FIX: Changed 'geom' to 'way' (osm2pgsql's default geometry column name)
-- FIX: Added ST_SetSRID to explicitly declare GPS coordinates (SRID 4326)
INSERT INTO routing_network.edges (source, target, cost, reverse_cost, geom, route_name, mode)
SELECT 
    NULL::BIGINT,
    NULL::BIGINT,
    ST_Length(ST_SetSRID(way, 4326)) / 1000.0 * 60.0 / 40.0 AS cost,
    ST_Length(ST_SetSRID(way, 4326)) / 1000.0 * 60.0 / 40.0 AS reverse_cost,
    ST_SetSRID(way, 4326) AS geom,
    tags->'name' AS route_name,
    'tro-tro'::TEXT AS mode
FROM planet_osm_line
WHERE 
    (tags->'highway' IN ('motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'living_street', 'service'))
    AND (tags->'access' IS NULL OR tags->'access' != 'no')
    AND (tags->'motor_vehicle' IS NULL OR tags->'motor_vehicle' != 'no');

-- 3. Generate the Routing Topology
SELECT pgr_createTopology('routing_network.edges', 0.0001, 'geom', 'id');

-- 4. Populate our Vertices table
INSERT INTO routing_network.vertices (id, geom, type)
SELECT id, the_geom, 'junction'
FROM routing_network.edges_vertices_pgr;

-- 5. Add Indexes for speed
CREATE INDEX IF NOT EXISTS idx_edges_source ON routing_network.edges (source);
CREATE INDEX IF NOT EXISTS idx_edges_target ON routing_network.edges (target);
CREATE INDEX IF NOT EXISTS idx_vertices_id ON routing_network.vertices (id);
