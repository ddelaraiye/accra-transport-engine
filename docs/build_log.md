📝 PROJECT BUILD LOG: Accra Informal Transport Decision Engine
Log Entry 001: Environment Architecture & Setup
Date: [Current Date: 1st May, 2026]
Phase: Infrastructure Setup

🎯 Objective
To establish a localized, enterprise-grade database environment on a personal PC without dealing with complex manual configurations, ensuring the project can be easily replicated by examiners or future developers.

🧠 Logic & Reasoning (Why we did it this way)
The Problem: Traditional routing requires installing PostgreSQL, installing the PostGIS extension, installing the routing extension (pgRouting), and configuring environment variables. If one setting is wrong, the whole system crashes. Furthermore, if you build it on your PC, it might not work on your examiner's PC.
The Solution: We chose Docker. Docker packages an application and all its dependencies into a standardized, isolated unit called a "container."
The Analogy: Instead of buying the wood, nails, and tools to build a house from scratch on every new plot of land (manual installation), we are shipping a pre-built, fully furnished mobile home (Docker container) that just needs to be plugged into electricity.
🛠️ Execution Steps
Enabled Virtualization: Told the computer's motherboard (BIOS) to allow running "virtual computers" inside the main computer (required for Docker on Windows).
Installed WSL 2 (Windows Subsystem for Linux): Docker on Windows runs best on a lightweight Linux background system. We installed this via the command wsl --install.
Installed Docker Desktop: Downloaded the official Docker interface to manage our containers.
🚨 Errors Encountered & Fixes
Error 1: Upon opening WSL, terminal showed multiple red wsl: Failed to translate... errors pointing to folders like E:\ArcGIS\... and D:\1Tienaah\New folder\...
Root Cause: WSL was trying to read Windows system PATH variables that had spaces or special characters in their file paths.
Fix: Ignored completely. This is a known, harmless Microsoft bug. It does not affect Docker or our database in any way.
Error 2: Docker Desktop installation failed with popup: "For security reasons C:\ProgramData\DockerDesktop must be owned by an elevated account."
Root Cause: A leftover folder from a previously failed installation attempt existed, and Windows security prevented the new installer from overwriting it.
Fix: Forced ownership of the folder via an Administrator Command Prompt:
Took ownership: takeown /F "C:\ProgramData\DockerDesktop" /R /D Y
Granted permissions: icacls "C:\ProgramData\DockerDesktop" /grant administrators:F /T
Deleted the folder: rmdir /S /Q "C:\ProgramData\DockerDesktop"
Re-ran the installer as Administrator.
✅ Validation
Docker Desktop opened successfully. The bottom-left status bar turned green with the text: "Engine running". The local server environment is now active.

Log Entry 002: Database Initialization (The Blueprint)
Date: [Current Date]
Phase: Infrastructure Setup

🎯 Objective
To create the actual database structure that will hold Accra's transport map and enable fast mathematical pathfinding (routing).

🧠 Logic & Reasoning
Why PostGIS? Standard databases (like SQLite or basic PostgreSQL) treat location as just text (e.g., "Circle"). PostGIS treats location as actual geometry (points, lines on a grid). This allows us to ask mathematical questions like "Find all stops within 500 meters of this point."
Why pgRouting? Instead of writing complex pathfinding algorithms (like Dijkstra's) in Python from scratch, pgRouting adds routing functions directly into the database. We just ask the database: "Find the shortest path from A to B," and it returns the answer instantly.
The init_db.sql file: We wrote a setup script that runs automatically the very first time the database turns on. It creates two tables: vertices (the stops/nodes) and edges (the road segments connecting them).
🛠️ Execution Steps
Created docker-compose.yml: The instruction manual telling Docker to download the postgis/postgis:15-3.3 image and map it to local port 5432.
Created scripts/init_db.sql: The SQL script containing CREATE EXTENSION postgis, CREATE EXTENSION pgrouting, and the table schemas for routing_network.edges and routing_network.vertices.
🚨 Errors Encountered & Fixes
None at this stage. Blueprints do not error until built.
✅ Validation
Pending. (Requires running the Docker container).