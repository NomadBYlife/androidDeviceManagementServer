#!/usr/bin/env bash
. ~/remote_lib/emulator_functions.sh
me="stop remote cloud-default-v2"
check_port_param_passed ${@}
port=${1}

check_port_process_for_emu ${port} 15
if [[ ${?} != 0 ]]
then
    echo -e "Emulator NOT running on port ${port}"
    # Sometime emulators are stuck and not listening on any port. So lets make sure we kill those as well
    pid=$( get_pid_emu_from_port ${port} )
    echo "But process is running"
    [ "$pid" != "" ] && kill_pid ${pid} 0
    exit 2
fi

pid=$( get_pid_emu_from_port ${port} )
kill_pid ${pid} 0
if [[ ${?} != 0 ]]
then
    fail ${me} ${@}
fi

echo -e "Emulator NOT running on port ${port}"
exit 2
