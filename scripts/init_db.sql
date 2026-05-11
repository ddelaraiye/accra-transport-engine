-- Enable the spatial and routing engines
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;

-- Create the schema for our decision engine
CREATE SCHEMA IF NOT EXISTS routing_network;

-- Create the Edges table (The roads/routes tro-tros travel)
CREATE TABLE routing_network.edges (
    id SERIAL PRIMARY KEY,
    source BIGINT,
    target BIGINT,
    cost DOUBLE PRECISION,
    reverse_cost DOUBLE PRECISION,
    geom GEOMETRY(LINESTRING, 4326),
    route_name TEXT,
    mode TEXT DEFAULT 'tro-tro'
);

-- Create the Vertices table (The stops/junctions)
CREATE TABLE routing_network.vertices (
    id BIGINT PRIMARY KEY,
    osm_id BIGINT,
    name TEXT,
    geom GEOMETRY(POINT, 4326),
    type TEXT 
);

-- Add spatial indexes (This is what makes PostGIS fast)
CREATE INDEX idx_edges_geom ON routing_network.edges USING GIST(geom);
CREATE INDEX idx_vertices_geom ON routing_network.vertices USING GIST(geom);

-- Confirm setup
DO $$ BEGIN
    RAISE NOTICE 'PostGIS & pgRouting Decision Engine Initialized Successfully.';
END $$;