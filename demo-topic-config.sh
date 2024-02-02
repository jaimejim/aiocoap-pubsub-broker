#!/usr/bin/env fish

function execute_command
    set -l command $argv[1]
    printf  "request > "$command 
    while true
        read -n 1 -s key
        if test -z "$key"
            break
        end
    end
    printf '\e[34m%s\e[m\n' "response >" # print in blue
    eval $command
end

set -l domain $argv[1]


echo
printf "1. Create a new topic-configuration resource\n"
execute_command "./client.py -m POST coap://$domain/ps --payload \"{\\\"topic-name\\\": \\\"Tradfi Light\\\", \\\"resource-type\\\": \\\"core.ps.conf\\\", \\\"media-type\\\": \\\"application/json\\\", \\\"topic-type\\\": \\\"temperature\\\", \\\"expiration-date\\\": \\\"2023-04-05T23:59:59Z\\\", \\\"max-subscribers\\\": 123, \\\"observer-check\\\": 86400}\""
echo
printf "2. Find any topic-configurations with specific characteristics\n"
execute_command "./client.py -m FETCH 'coap://$domain/ps' --content-format 'application/cbor' --payload '{\"max-subscribers\": 123}'"
echo