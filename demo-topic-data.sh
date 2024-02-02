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
printf "1. Discover the broker's topic-config resources\n"
execute_command "./client.py -m GET \"coap://$domain/.well-known/core?rt=core.ps.conf\""
echo
printf "2. Discover the broker's topic-data resources\n"
execute_command "./client.py -m GET \"coap://$domain/.well-known/core?rt=core.ps.data\""
echo
printf "3. Read latest resource value\n"
execute_command "./client.py -m GET coap://$domain/ps/data/0000003"
echo
printf "4. Subscribe to all values\n"
execute_command "./client.py -m GET --observe coap://$domain/ps/data/all"
echo