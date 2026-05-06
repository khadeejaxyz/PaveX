# Database Schema

PaveX primarily uses in-memory storage for real-time operations with browser localStorage for persistence. However, for extended functionality (historical analytics, multi-vehicle sharing), a database schema would be:

## Core Tables

### detections
```
+------------------+--------------+------+-----+-------------------+----------------+
| Field            | Type         | Null | Key | Default           | Extra          |
+------------------+--------------+------+-----+-------------------+----------------+
| id               | VARCHAR(36)  | NO   | PRI | UUID()            |                |
| timestamp        | DATETIME     | NO   |     | CURRENT_TIMESTAMP |                |
| latitude         | DECIMAL(9,6) | YES  |     | NULL              |                |
| longitude        | DECIMAL(9,6) | YES  |     | NULL              |                |
| hazard_type      | ENUM('pothole', 'speed_hump') | NO |     | NULL              |                |
| confidence       | FLOAT        | NO   |     | NULL              |                |
| severity         | ENUM('low', 'medium', 'high') | NO |     | NULL              |                |
| speed_recommendation | INT       | YES  |     | NULL              |                |
| bbox_x1          | FLOAT        | YES  |     | NULL              |                |
| bbox_y1          | FLOAT        | YES  |     | NULL              |                |
| bbox_x2          | FLOAT        | YES  |     | NULL              |                |
| bbox_y2          | FLOAT        | YES  |     | NULL              |                |
| vehicle_id       | VARCHAR(36)  | YES  | MUL | NULL              |                |
| session_id       | VARCHAR(36)  | YES  | MUL | NULL              |                |
| processed        | BOOLEAN      | NO   |     | FALSE             |                |
+------------------+--------------+------+-----+-------------------+----------------+
```

### vehicles
```
+------------+--------------+------+-----+---------+----------------+
| Field      | Type         | Null | Key | Default | Extra          |
+------------+--------------+------+-----+---------+----------------+
| id         | VARCHAR(36)  | NO   | PRI | UUID()  |                |
| name       | VARCHAR(100) | YES  |     | NULL    |                |
| type       | VARCHAR(50)  | YES  |     | NULL    |                |
| created_at | DATETIME     | NO   |     | CURRENT_TIMESTAMP |              |
| updated_at | DATETIME     | NO   |     | CURRENT_TIMESTAMP | ON UPDATE      |
+------------+--------------+------+-----+---------+----------------+
```

### sessions
```
+------------+--------------+------+-----+-------------------+----------------+
| Field      | Type         | Null | Key | Default           | Extra          |
+------------+--------------+------+-----+-------------------+----------------+
| id         | VARCHAR(36)  | NO   | PRI | UUID()            |                |
| vehicle_id | VARCHAR(36)  | NO   | MUL | NULL              |                |
| start_time | DATETIME     | NO   |     | CURRENT_TIMESTAMP |                |
| end_time   | DATETIME     | YES  |     | NULL              |                |
| total_distance | FLOAT    | YES  |     | NULL              |                |
| avg_speed  | FLOAT        | YES  |     | NULL              |                |
| created_at | DATETIME     | NO   |     | CURRENT_TIMESTAMP |                |
+------------+--------------+------+-----+-------------------+----------------+
```

### hazard_reports
```
+----------------+--------------+------+-----+-------------------+----------------+
| Field          | Type         | Null | Key | Default           | Extra          |
+----------------+--------------+------+-----+-------------------+----------------+
| id             | VARCHAR(36)  | NO   | PRI | UUID()            |                |
| detection_id   | VARCHAR(36)  | NO   | MUL | NULL              |                |
| reporter_id    | VARCHAR(36)  | YES  | MUL | NULL              |                |
| verified       | BOOLEAN      | NO   |     | FALSE             |                |
| verification_notes | TEXT     | YES  |     | NULL              |                |
| verified_at    | DATETIME     | YES  |     | NULL              |                |
| created_at     | DATETIME     | NO   |     | CURRENT_TIMESTAMP |                |
+----------------+--------------+------+-----+-------------------+----------------+
```

## Relationships
- `detections.vehicle_id` → `vehicles.id`
- `detections.session_id` → `sessions.id`
- `sessions.vehicle_id` → `vehicles.id`
- `hazard_reports.detection_id` → `detections.id`
- `hazard_reports.reporter_id` → `users.id` (if user system implemented)

## Indexes
- Primary keys on all ID fields
- Index on `detections.timestamp` for time-range queries
- Index on `detections.hazard_type` and `detections.severity` for filtering
- Index on `detections.latitude`, `detections.longitude` for spatial queries
- Composite index on `(detections.timestamp, detections.hazard_type)`

## Storage Considerations
- For production deployment with multiple vehicles:
  - Use PostgreSQL with PostGIS extension for spatial queries
  - Implement partitioning by date for large detection tables
  - Use read replicas for analytics workloads
  - Implement archival strategy for old detection data
- For single-vehicle/deployment:
  - SQLite sufficient for local persistence
  - Browser IndexedDB as alternative to localStorage for larger datasets
