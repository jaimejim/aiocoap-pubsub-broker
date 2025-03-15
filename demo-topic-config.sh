#!/usr/bin/env bash

execute_command() {
    local command="$1"
    echo "$command "
    read -n 1 -s -r -p $'\e[1;33m\e[0m'
    echo "\n"
    if [[ "$command" == *"application/json"* ]]; then
        eval "$command" | jq .
    else
        eval "$command"
    fi
}

domain="$1"

echo
echo $'\e[1;32m- Create a new topic-configuration resource \e[0m'
execute_command "poetry run python3 client.py -m POST coap://$domain/ps --payload '{\"topic-name\": \"Tradfi Light\", \"resource-type\": \"core.ps.conf\", \"media-type\": \"application/json\", \"topic-type\": \"temperature\", \"expiration-date\": \"2023-04-05T23:59:59Z\", \"max-subscribers\": 123, \"observer-check\": 86400}'"
echo
echo $'\e[1;32m- Find any topic-configurations with specific characteristics \e[0m'
execute_command "poetry run python3 client.py -m FETCH coap://$domain/ps --content-format application/cbor --payload '{\"max-subscribers\": 123}'"
echo