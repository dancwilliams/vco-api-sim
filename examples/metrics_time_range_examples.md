# Metrics Time Range Examples

The VCO API Simulator now supports custom time ranges and intervals for time series metrics endpoints.

## Query Parameters

- `start`: Start time for the metrics range
- `end`: End time for the metrics range
- `interval`: Data point interval in minutes (1-60, defaults to 5)

## Supported Time Formats

### 1. Unix Timestamp (milliseconds)
```bash
# Get last 6 hours of health metrics
START=$(date -d '6 hours ago' +%s%3N)
END=$(date +%s%3N)
curl "http://localhost:8000/api/sdwan/v2/enterprises/ent-1/edges/edge-1/healthStats/timeSeries?start=${START}&end=${END}"
```

### 2. ISO 8601 Format
```bash
# Get metrics from 2024-01-30 12:00 to 18:00 UTC
curl "http://localhost:8000/api/sdwan/v2/enterprises/ent-1/edges/edge-1/healthStats/timeSeries?start=2024-01-30T12:00:00Z&end=2024-01-30T18:00:00Z"
```

## Examples

### Default Behavior (Last 1 Hour, 5-Minute Intervals)
```bash
curl "http://localhost:8000/api/sdwan/v2/enterprises/ent-1/edges/edge-1/healthStats/timeSeries"
```
Returns: ~12 data points (60 minutes ÷ 5-minute intervals)

### Custom Time Range (Last 6 Hours)
```bash
# Using ISO 8601
START_TIME=$(date -u -d '6 hours ago' +%Y-%m-%dT%H:%M:%SZ)
END_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
curl "http://localhost:8000/api/sdwan/v2/enterprises/ent-1/edges/edge-1/healthStats/timeSeries?start=${START_TIME}&end=${END_TIME}"
```
Returns: ~72 data points (360 minutes ÷ 5-minute intervals)

### Custom Interval (Last 1 Hour, 10-Minute Intervals)
```bash
curl "http://localhost:8000/api/sdwan/v2/enterprises/ent-1/edges/edge-1/healthStats/timeSeries?interval=10"
```
Returns: ~6 data points (60 minutes ÷ 10-minute intervals)

### Custom Time Range + Custom Interval (Last 24 Hours, 30-Minute Intervals)
```bash
START_TIME=$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)
END_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
curl "http://localhost:8000/api/sdwan/v2/enterprises/ent-1/edges/edge-1/linkStats/timeSeries?start=${START_TIME}&end=${END_TIME}&interval=30"
```
Returns: ~48 data points (1440 minutes ÷ 30-minute intervals)

### Only End Time Specified (1 Hour Before End)
```bash
END_TIME=$(date -u -d '2 hours ago' +%Y-%m-%dT%H:%M:%SZ)
curl "http://localhost:8000/api/sdwan/v2/enterprises/ent-1/edges/edge-1/healthStats/timeSeries?end=${END_TIME}"
```
Returns: Data from 3 hours ago to 2 hours ago (1 hour window)

## Supported Endpoints

- `/api/sdwan/v2/enterprises/{enterpriseLogicalId}/edges/{edgeLogicalId}/healthStats/timeSeries`
- `/api/sdwan/v2/enterprises/{enterpriseLogicalId}/edges/{edgeLogicalId}/linkStats/timeSeries`

## Response Format

```json
{
  "_href": "/api/sdwan/v2/enterprises/ent-1/edges/edge-1/healthStats/timeSeries",
  "total": 72,
  "series": [
    {
      "time": 1706619600000,
      "cpuPct": 45.2,
      "memoryPct": 62.5,
      "tunnelCount": 8,
      "flowCount": 2400
    },
    {
      "time": 1706619900000,
      "cpuPct": 47.1,
      "memoryPct": 63.2,
      "tunnelCount": 8,
      "flowCount": 2450
    }
    // ... more data points
  ]
}
```

## Notes

- If `start >= end`, the times will be automatically swapped
- Invalid time formats fall back to default (last 1 hour)
- Interval is clamped between 1-60 minutes
- All timestamps in responses are Unix milliseconds
- Times are interpreted as UTC
