# JALDRISHTI AI — Database Security, PostGIS & Integrity Architecture

## 1. Relational Integrity & Schema Design
The database layer uses normalized 3NF relational schemas with strict integrity guarantees:
- **Foreign Keys**: `ON DELETE CASCADE` ensures child records (subscriptions, tokens, preferences) are cleaned up cleanly when parent users are deleted.
- **CHECK Constraints**: Validate geographical ranges (`latitude BETWEEN -90 AND 90`, `longitude BETWEEN -180 AND 180`), severity enums, and boolean flags.
- **Atomicity & Isolation**: Every multi-statement mutation runs inside strict transactions with rollback guarantees on failure.

---

## 2. PostGIS Spatial Architecture (Production)
- Uses PostGIS spatial geometries (`geometry(Point, 4326)`) and 2D R-Tree indexes (`GIST`) for microsecond-scale point-in-polygon matching against flood extent polygons.
- Local development retains high-performance SQLite WAL mode with Haversine spherical math.

---

## 3. Defense Against SQL Injection
- String interpolation (`f"SELECT * FROM ... {input}"`) is strictly prohibited.
- All repository queries use parameterized bindings (`?` for SQLite, `%s` / `$1` for PostgreSQL).
