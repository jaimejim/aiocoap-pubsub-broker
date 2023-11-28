#!/usr/bin/env fish

# Take the broker domain as an input from the command line
if set -q argv[1]
    set broker_domain $argv[1]
else
    echo "Please provide the broker domain as an argument."
    exit 1
end

set broker_url "coap://$broker_domain"


# Array of topic configurations
set topic_configurations "{
    \"topic-name\": \"All Sensors\",
    \"topic-data\": \"mytopic\",
    \"resource-type\": \"core.ps.conf\",
    \"media-type\": \"application/json\",
    \"topic-type\": \"opaque\",
    \"expiration-date\": \"2024-04-05T23:59:59Z\",
    \"max-subscribers\": 200,
    \"observer-check\": 86400
}" "{
    \"topic-name\": \"Temperature Sensor\",
    \"topic-data\": \"ps/data/0000001\",
    \"resource-type\": \"core.ps.conf\",
    \"media-type\": \"application/json\",
    \"topic-type\": \"temperature\",
    \"expiration-date\": \"2024-04-05T23:59:59Z\",
    \"max-subscribers\": 300,
    \"observer-check\": 86400
}" "{
    \"topic-name\": \"Humidity Sensor\",
    \"topic-data\": \"ps/data/0000002\",
    \"resource-type\": \"core.ps.conf\",
    \"media-type\": \"application/json\",
    \"topic-type\": \"temperature\",
    \"expiration-date\": \"2024-04-05T23:59:59Z\",
    \"max-subscribers\": 200,
    \"observer-check\": 86400
}" "{
    \"topic-name\": \"Humidity Sensor\",
    \"topic-data\": \"ps/data/0000003\",
    \"resource-type\": \"core.ps.conf\",
    \"media-type\": \"application/json\",
    \"topic-type\": \"humidity\",
    \"expiration-date\": \"2024-04-05T23:59:59Z\",
    \"max-subscribers\": 400,
    \"observer-check\": 86400
}" "{
    \"topic-name\": \"Light Sensor\",
    \"topic-data\": \"ps/data/0000004\",
    \"resource-type\": \"core.ps.conf\",
    \"media-type\": \"application/json\",
    \"topic-type\": \"light\",
    \"expiration-date\": \"2024-04-05T23:59:59Z\",
    \"max-subscribers\": 200,
    \"observer-check\": 86400
}" "{
    \"topic-name\": \"Air Quality Sensor\",
    \"topic-data\": \"ps/data/0000005\",
    \"resource-type\": \"core.ps.conf\",
    \"media-type\": \"application/json\",
    \"topic-type\": \"air-quality\",
    \"expiration-date\": \"2024-04-05T23:59:59Z\",
    \"max-subscribers\": 60,
    \"observer-check\": 86400
}"

# Loop over the topic configurations
for config in $topic_configurations
    # Send a POST request for each topic configuration
    ./client.py -m POST $broker_url/ps --payload $config
end


while true

    # Generate random values for each sensor
    set temperature (math (random 10 40))
    set humidity1 (math (random 20 70))
    set humidity2 (math (random 20 70))
    set light (math (random 100 1100))
    set air_quality (math (random 100 600))

    # Publish data for each sensor at random intervals

    # Temperature sensor data
    ./client.py -m PUT coap://$broker_domain/ps/data/0000001 --payload "{\"n\": \"urn:uuid:ec3c1208-5825-4839-b5bf-2d3f024b223a\",\"u\": \"Cel\",\"t\": \""(date -u +'%Y-%m-%dT%H:%M:%SZ')"\",\"v\": $temperature}"
    ./client.py -m PUT coap://$broker_domain/mytopic --payload "{\"n\": \"urn:uuid:ec3c1208-5825-4839-b5bf-2d3f024b223a\",\"u\": \"Cel\",\"t\": \""(date -u +'%Y-%m-%dT%H:%M:%SZ')"\",\"v\": $temperature}"
    sleep (math (random 1 5))

    # Humidity sensor 1 data
    ./client.py -m PUT coap://$broker_domain/ps/data/0000002 --payload "{\"n\": \"urn:uuid:7876e1f5-328a-46dc-b539-5abfbdb226d3\",\"u\": \"%RH\",\"t\": \""(date -u +'%Y-%m-%dT%H:%M:%SZ')"\",\"v\": $humidity1}"
    ./client.py -m PUT coap://$broker_domain/mytopic --payload "{\"n\": \"urn:uuid:7876e1f5-328a-46dc-b539-5abfbdb226d3\",\"u\": \"%RH\",\"t\": \""(date -u +'%Y-%m-%dT%H:%M:%SZ')"\",\"v\": $humidity1}"
    sleep (math (random 2 6))

    # Humidity sensor 2 data
    ./client.py -m PUT coap://$broker_domain/ps/data/0000003 --payload "{\"n\": \"urn:uuid:355b1fe3-9608-4702-8a6f-92084cd9ebe3\",\"u\": \"%RH\",\"t\": \""(date -u +'%Y-%m-%dT%H:%M:%SZ')"\",\"v\": $humidity2}"
    ./client.py -m PUT coap://$broker_domain/mytopic --payload "{\"n\": \"urn:uuid:355b1fe3-9608-4702-8a6f-92084cd9ebe3\",\"u\": \"%RH\",\"t\": \""(date -u +'%Y-%m-%dT%H:%M:%SZ')"\",\"v\": $humidity2}"
    sleep (math (random 8 14))

    # Light sensor data
    ./client.py -m PUT coap://$broker_domain/ps/data/0000004 --payload "{\"n\": \"lurn:uuid:cef3dfc7-cf53-4a27-907e-4de3584697be\",\"u\": \"Lux\",\"t\": \""(date -u +'%Y-%m-%dT%H:%M:%SZ')"\",\"v\": $light}"
    ./client.py -m PUT coap://$broker_domain/mytopic --payload "{\"n\": \"lurn:uuid:cef3dfc7-cf53-4a27-907e-4de3584697be\",\"u\": \"Lux\",\"t\": \""(date -u +'%Y-%m-%dT%H:%M:%SZ')"\",\"v\": $light}"
    sleep (math (random 4 10))

    # Air quality sensor data
    ./client.py -m PUT coap://$broker_domain/ps/data/0000005 --payload "{\"n\": \"urn:uuid:c2b2470f-96d7-42c7-9a14-2866ed2c75eb\",\"u\": \"ppm\",\"t\": \""(date -u +'%Y-%m-%dT%H:%M:%SZ')"\",\"v\": $air_quality}"
    ./client.py -m PUT coap://$broker_domain/mytopic --payload "{\"n\": \"urn:uuid:c2b2470f-96d7-42c7-9a14-2866ed2c75eb\",\"u\": \"ppm\",\"t\": \""(date -u +'%Y-%m-%dT%H:%M:%SZ')"\",\"v\": $air_quality}"
    sleep (math (random 2 6))

end
