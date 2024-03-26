#!/bin/bash

# Path to the log file
# shellcheck disable=SC1007
logFile= "/mnt/c/Users/Roy Avrahami/PycharmProjects/sensorz_qa_roy/logs/scanner_rf.log.4"

# Extract lines that contain 'Data Processed'
# shellcheck disable=SC2154
processedDataLines=$(grep 'Data Processed' "$logFile")

# Count the number of 'Data Processed' events
totalEvents=$(echo "$processedDataLines" | wc -l)

# Assuming the log's first and last 'Data Processed' entries can give us the time span
startTime=$(echo "$processedDataLines" | head -1 | awk '{print $1, $2}')
endTime=$(echo "$processedDataLines" | tail -1 | awk '{print $1, $2}')

# Convert timestamps to seconds since the epoch
startSec=$(date -d "$startTime" +%s)
endSec=$(date -d "$endTime" +%s)

# Calculate duration in seconds
duration=$((endSec - startSec))

# Calculate the rate of data processing events per second (avoid division by zero)
if [ $duration -gt 0 ]; then
    rate=$(echo "scale=2; $totalEvents / $duration" | bc)
    echo "Data Processing Rate: $rate events per second"
else
    echo "Cannot calculate the rate. Duration is zero or undefined."
fi
