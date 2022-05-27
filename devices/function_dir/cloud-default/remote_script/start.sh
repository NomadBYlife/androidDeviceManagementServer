#!/usr/bin/env bash
#set -o xtrace
emulator_params=( was not set correctly )
. ~/remote_lib/emulator_functions.sh
me="start remote cloud-default-v2"
check_display_env
check_port_param_passed ${@}
port=${1}
complex_emu_params

# check if its running
check_port_process_for_emu ${port} 15
if [[ ${?} == 0 ]]
then
    echo -e "Emulator running on port ${port}"
    exit 0
fi

export PATH=$PATH:/home/kobil/Android/Sdk/emulator
which emulator &> /dev/null
if [[ ${?} != 0 ]]
then
    echo -e "This host does not have the emulator executable where this script expects it to be!"
    fail ${me} ${@}
fi

# sadly this executable dumps many useless error/status messages even when executing successfully
emulator @emulator${port} -port $((${port}-1)) ${emulator_params[@]} &> /dev/null &

# doesn't return so no retval to check, but let's check if its running somehow
check_port_process_for_emu ${port} 0
if [[ ${?} != 0 ]]
then
    echo -e "Emulator NOT running on port ${port}"
    exit 2
fi

# the adb executable does something wierd so we have to wrap all adb calls in another function because black magic
function rest_of_main(){
wait_for_device $((${port}-1))
if [[ ${?} != 0 ]]
then
    echo -e "Emulator on port ${port} in undefined state"
    exit 1
fi
sleep 10
# dont rush ... emulator acts funny if we dont wait a lil
unlock_device $((${port}-1))

echo -e "Emulator running on port ${port}"
return 0
}
rest_of_main