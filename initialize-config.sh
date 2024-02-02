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
    \"topic-data\": \"ps/data/all\",
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
