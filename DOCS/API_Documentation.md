# API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### Health & Status
**GET /**  
- Description: Basic health check endpoint
- Response:
  ```json
  {
    "status": "online",
    "system": "PaveX Backend API"
  }
  ```
- Status Codes:
  - 200: OK

**GET /test**  
- Description: Detailed backend connectivity test
- Response:
  ```json
  {
    "status": "ok",
    "message": "PaveX Backend is reachable",
    "timestamp": 1640995200.123
  }
  ```
- Status Codes:
  - 200: OK

**GET /stats**  
- Description: Get real-time detection statistics
- Response:
  ```json
  {
    "potholes": 124,
    "humps": 87,
    "high_severity": 23,
    "avg_confidence": 0.842
  }
  ```
- Status Codes:
  - 200: OK
  - 500: Internal server error (model not loaded)

### Detection
**POST /detect**  
- Description: Process a single frame for hazard detection
- Request Body:
  ```json
  {
    "data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
  }
  ```
- Response (Success):
  ```json
  {
    "detections": [
      {
        "class": "pothole",
        "confidence": 0.92,
        "severity": "high",
        "speed_recommendation": 20,
        "bbox": [120.5, 85.3, 200.7, 150.2]
      }
    ],
    "inference_time": 45.2,
    "fps": 22.1
  }
  ```
- Response (Error):
  ```json
  {
    "error": "Missing image data"
  }
  ```
- Status Codes:
  - 200: OK
  - 400: Bad request (invalid or missing data)
  - 500: Internal server error (processing failure)

#### WebSocket Endpoints

**WS /ws**  
- Description: Primary real-time communication channel
- Message Types:
  
  Client → Server:
  ```json
  {
    "type": "frame",
    "data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
    "timestamp": 1640995200123
  }
  ```
  
  Server → Client:
  ```json
  {
    "type": "detections",
    "data": [
      {
        "class": "pothole",
        "confidence": 0.92,
        "severity": "high",
        "speed_recommendation": 20,
        "bbox": [120.5, 85.3, 200.7, 150.2]
      }
    ],
    "timestamp": 1640995200456
  }
  ```
  
  Server → Client (Statistics):
  ```json
  {
    "type": "stats",
    "data": {
      "potholes": 124,
      "humps": 87,
      "high_severity": 23,
      "avg_confidence": 0.842
    },
    "timestamp": 1640995200500
  }
  ```
  
  Server → Client (Heartbeat):
  ```json
  {
    "type": "heartbeat",
    "timestamp": 1640995200600
  }
  ```

**WS /ws/alerts**  
- Description: Legacy WebSocket endpoint for direct frame processing (maintained for backward compatibility)
- Message format identical to `/ws`

## Error Responses
All endpoints return JSON error responses with the following structure:
```json
{
  "error": "Human-readable error message"
}
```

Common HTTP status codes:
- 400: Bad Request (client error)
- 401: Unauthorized (authentication required)
- 403: Forbidden (insufficient permissions)
- 404: Not Found (endpoint doesn't exist)
- 429: Too Many Requests (rate limiting)
- 500: Internal Server Error
- 503: Service Unavailable (temporary overload)

## Rate Limits
- `/detect` endpoint: 30 requests/second per IP
- WebSocket connections: 10 concurrent connections per IP
- Exceeding limits returns 429 status with retry-after header

## Versioning
API version implied in URL path (e.g., `/api/v1/detect`) - planned for future iterations
