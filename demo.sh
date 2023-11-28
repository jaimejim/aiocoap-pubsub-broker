#!/usr/bin/env fish

function execute_command
    set -l command $argv[1]
    printf '\e[32m%s\e[m\n' "request > "$command # print in green
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

execute_command "./client.py -m GET coap://$domain/.well-known/core"
execute_command "./client.py -m GET coap://$domain/ps"
execute_command "./client.py -m GET coap://$domain/ps/8ff2ee | jq"
execute_command "./client.py -m GET --observe coap://$domain/ps/data/0000003"
execute_command "./client.py -m GET --observe coap://$domain/ps/data/0000005"
execute_command "./client.py -m GET coap://$domain/ps/63c11f | jq"
execute_command "./client.py -m GET \"coap://$domain/.well-known/core?rt=core.ps.conf\""
execute_command "./client.py -m GET \"coap://$domain/.well-known/core?rt=core.ps.data\""
execute_command "./client.py -m GET coap://$domain/.well-known/core?rt=core.ps.data"