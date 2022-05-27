#!/usr/bin/env bash
. ~/remote_lib/emulator_functions.sh
me="status remote cloud-default"
check_port_param_passed ${@}
port=${1}

# check if its running
check_port_process_for_emu ${port} 0
if [[ ${?} -ne 0 ]]
then
    echo -e "Emulator NOT running on port ${port}"
    exit 2
else
    # check if it is unlocked
    check_locked_state_unlocked $((${port}-1))
    if [[ ${?} -ne 0 ]]
    then
        echo -e "Emulator LOCKED and running on port ${port}"
        exit 3
    else
        echo -e "Emulator running on port ${port}"
        exit 0
    fi
fi
