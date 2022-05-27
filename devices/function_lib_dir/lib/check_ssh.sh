#!/usr/bin/env bash

ssh -o "BatchMode yes" -o "ConnectTimeout 3" -o "StrictHostKeyChecking no"  ${user}@${ip} exit
ret_val=${?}
if  [[ ${ret_val} != 0 ]]
then
    echo -e "Error! Failed to establish ssh connection to ${user}@${ip}" >&2
    exit ${ret_val}
fi
