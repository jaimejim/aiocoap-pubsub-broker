#!/usr/bin/env bash

echo $'\e[1;32m- Initializing demo topics ✅ \e[0m'
sh initialize-config.sh iot.dev > /dev/null 2>&1 &
config_pid=$!
sh initialize-data.sh iot.dev > /dev/null 2>&1 &
data_pid=$!

# Store all background process IDs
pids=("$config_pid" "$data_pid")

# Set a process group for the script
trap 'cleanup' EXIT SIGINT SIGTERM

cleanup() {
    echo $'\e[1;31m- Cleaning up background processes... \e[0m'
    
    # Kill all processes in the same process group
    kill -- -$$ 2>/dev/null
}

execute_command() {
    local command="$1"
    echo "$command "
    read -n 1 -s -r -p $'\e[1;33mPress any key to continue...\e[0m'
    echo "\n"
    
    if [[ "$command" == *"--observe"* ]]; then
        # Run observation command in the background
        eval "$command" &
        observe_pid=$!
        pids+=("$observe_pid")
    elif [[ "$command" == *"application/json"* ]]; then
        eval "$command" | jq .
    else
        eval "$command"
    fi
}

domain="$1"

echo $'\e[1;32m- Create a new topic-configuration resource \e[0m'
echo "Request: POST /ps"
echo "Payload: {\"topic-name\": \"Tradfi Light\", \"resource-type\": \"core.ps.conf\", \"media-type\": \"application/json\", \"topic-type\": \"temperature\", \"expiration-date\": \"2023-04-05T23:59:59Z\", \"max-subscribers\": 123, \"observer-check\": 86400}"
echo "----------------------------------------->"
execute_command "poetry run python3 client.py -m POST coap://$domain/ps --payload '{\"topic-name\": \"Tradfi Light\", \"resource-type\": \"core.ps.conf\", \"media-type\": \"application/json\", \"topic-type\": \"temperature\", \"expiration-date\": \"2023-04-05T23:59:59Z\", \"max-subscribers\": 123, \"observer-check\": 86400}'"
echo
echo $'\e[1;32m- Find any topic-configurations with specific characteristics \e[0m'
echo "Request: FETCH /ps"
echo "Payload: {\"max-subscribers\": 123}"
echo "----------------------------------------->"
execute_command "poetry run python3 client.py -m FETCH coap://$domain/ps --content-format application/cbor --payload '{\"max-subscribers\": 123}'"
echo

echo $'\e[1;32m- Discover the broker\'s topic-config resources \e[0m'
echo "Request: GET /.well-known/core?rt=core.ps.conf"
echo "----------------------------------------->"
execute_command "poetry run python3 client.py -m GET \"coap://$domain/.well-known/core?rt=core.ps.conf\""
echo
echo $'\e[1;32m- Discover the broker\'s topic-data resources \e[0m'
echo "Request: GET /.well-known/core?rt=core.ps.data"
echo "----------------------------------------->"
execute_command "poetry run python3 client.py -m GET \"coap://$domain/.well-known/core?rt=core.ps.data\""
echo
echo $'\e[1;32m- Read latest resource value \e[0m'
echo "Request: GET /ps/data/0000003"
echo "----------------------------------------->"
execute_command "poetry run python3 client.py -m GET coap://$domain/ps/data/0000003"
echo
echo $'\e[1;32m- Subscribe to all values \e[0m'
echo "Request: GET /ps/data/all --observe"
echo "----------------------------------------->"
execute_command "poetry run python3 client.py -m GET --observe coap://$domain/ps/data/all"
echo

# Wait for all processes to complete
wait