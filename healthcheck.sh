#!/bin/bash
# Health check script for TrackRecord API
# Checks if API is responsive and restarts if not

HEALTH_URL="http://127.0.0.1:8000/health"
CONTAINER_NAME="trackrecord-api"
LOG_FILE="/var/log/trackrecord-healthcheck.log"

# Try to get health endpoint with 10 second timeout
RESPONSE=$(curl -s --max-time 10 "$HEALTH_URL" 2>/dev/null)

if echo "$RESPONSE" | grep -q "healthy"; then
    echo "$(date): API healthy" >> "$LOG_FILE"
else
    echo "$(date): API unhealthy, restarting container..." >> "$LOG_FILE"
    docker restart "$CONTAINER_NAME" >> "$LOG_FILE" 2>&1
    echo "$(date): Container restarted" >> "$LOG_FILE"
fi

# Keep log file from growing too large (keep last 1000 lines)
tail -1000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
