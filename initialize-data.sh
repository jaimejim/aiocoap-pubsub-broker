#!/usr/bin/env python3


# Take the broker domain as an input from the command line
if [ -n "$1" ]; then
    broker_domain="$1"
else
    echo "Please provide the broker domain as an argument."
    exit 1
fi

broker_url="coap://${broker_domain}"


while true; do

    # Generate random values for each sensor
    temperature=$((RANDOM % 31 + 10))
    humidity1=$((RANDOM % 51 + 20))
    humidity2=$((RANDOM % 51 + 20))
    light=$((RANDOM % 1001 + 100))
    air_quality=$((RANDOM % 31 + 100))

    # Publish data for each sensor at random intervals

    # Temperature sensor data
    poetry run ./client.py -m PUT "coap://${broker_domain}/ps/data/0000001" --payload "{\"n\": \"urn:uuid:ec3c1208-5825-4839-b5bf-2d3f024b223a\",\"u\": \"Cel\",\"t\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\",\"v\": $temperature}"
    poetry run ./client.py -m PUT "coap://${broker_domain}/ps/data/all" --payload "{\"n\": \"urn:uuid:ec3c1208-5825-4839-b5bf-2d3f024b223a\",\"u\": \"Cel\",\"t\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\",\"v\": $temperature}"
    sleep $((RANDOM % 5 + 1))

    # Humidity sensor 1 data
    poetry run ./client.py -m PUT "coap://${broker_domain}/ps/data/0000002" --payload "{\"n\": \"urn:uuid:7876e1f5-328a-46dc-b539-5abfbdb226d3\",\"u\": \"%RH\",\"t\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\",\"v\": $humidity1}"
    poetry run ./client.py -m PUT "coap://${broker_domain}/ps/data/all" --payload "{\"n\": \"urn:uuid:7876e1f5-328a-46dc-b539-5abfbdb226d3\",\"u\": \"%RH\",\"t\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\",\"v\": $humidity1}"
    sleep $((RANDOM % 5 + 2))

    # Humidity sensor 2 data
    poetry run ./client.py -m PUT "coap://${broker_domain}/ps/data/0000003" --payload "{\"n\": \"urn:uuid:355b1fe3-9608-4702-8a6f-92084cd9ebe3\",\"u\": \"%RH\",\"t\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\",\"v\": $humidity2}"
    poetry run ./client.py -m PUT "coap://${broker_domain}/ps/data/all" --payload "{\"n\": \"urn:uuid:355b1fe3-9608-4702-8a6f-92084cd9ebe3\",\"u\": \"%RH\",\"t\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\",\"v\": $humidity2}"
    sleep $((RANDOM % 7 + 8))

    # Light sensor data
    poetry run ./client.py -m PUT "coap://${broker_domain}/ps/data/0000004" --payload "{\"n\": \"lurn:uuid:cef3dfc7-cf53-4a27-907e-4de3584697be\",\"u\": \"Lux\",\"t\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\",\"v\": $light}"
    poetry run ./client.py -m PUT "coap://${broker_domain}/ps/data/all" --payload "{\"n\": \"lurn:uuid:cef3dfc7-cf53-4a27-907e-4de3584697be\",\"u\": \"Lux\",\"t\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\",\"v\": $light}"
    sleep $((RANDOM % 7 + 4))

    # Air quality sensor data
    poetry run ./client.py -m PUT "coap://${broker_domain}/ps/data/0000005" --payload "{\"n\": \"urn:uuid:c2b2470f-96d7-42c7-9a14-2866ed2c75eb\",\"u\": \"ppm\",\"t\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\",\"v\": $air_quality}"
    poetry run ./client.py -m PUT "coap://${broker_domain}/ps/data/all" --payload "{\"n\": \"urn:uuid:c2b2470f-96d7-42c7-9a14-2866ed2c75eb\",\"u\": \"ppm\",\"t\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\",\"v\": $air_quality}"
    sleep $((RANDOM % 5 + 2))

done
