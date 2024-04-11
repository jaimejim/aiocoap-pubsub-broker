#!/bin/bash

# Here coap://iot.dev is the hostname of the CoAP broker
if [ -z "$1" ]; then
  echo "Usage: $0 coap://iot.dev/ps/data/[path]"
  exit 1
fi

# Data path from the command line argument
DATA_PATH="$1"

# Initial value of v
V_INITIAL=0.0

# Counter for demonstration
COUNTER=0

# Number of increments/messages to send
NUM_INCREMENTS=80

while [ $COUNTER -lt $NUM_INCREMENTS ]; do
  
  V_VALUE=$(echo "$V_INITIAL + $COUNTER * 0.1" | bc)
  TIMESTAMP=$(date +%s)

  # Create the payload with the incremented v value (temperature in this case)
  PAYLOAD="{\"n\": \"temperature\",\"u\": \"Cel\",\"t\": $TIMESTAMP,\"v\": $V_VALUE}"

  echo "Sending payload: $PAYLOAD to $DATA_PATH"

  # I use poetry to run everything in a virtual environment
  poetry run ./client.py -m PUT "$DATA_PATH" --payload "$PAYLOAD"

  # Increment the counter
  ((COUNTER++))
done
