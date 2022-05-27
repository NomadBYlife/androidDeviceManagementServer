#!/usr/bin/env bash

function fail(){
    name=${1}
    shift 1
    echo -e "${name} script failed; parameters: ${@}"
    exit 1
}

function check_display_env(){
     export DISPLAY=:0
#    if [[ -z ${DISPLAY} ]]
#    then
#        # echo -e Display not set!
#        case "$(cat /etc/hostname)" in
#            "emulator-host-2")
#                ;;
#            "emulator-host1")
#                export DISPLAY=:0
#                ;;
#            "emulator")
#                export DISPLAY=:0
#                ;;
#            *)
#                fail ${me} ${@}
#                echo -e "Add some sensible logic for this host $(cat /etc/hostname) in the emulator functions!"
#                ;;
#        esac
#    fi
}

function emu_host_1_params(){
    emulator_params=( -no-snapshot-load -no-snapshot -no-boot-anim -gpu on -cores 4 \
         -net-tap emu-tap-${port} -dns-server 10.10.0.25,10.10.0.26 )
}

function emu_host_2_params(){
    if [[ ${port} -ge 5568 ]]
    then
#        emulator_params=( -no-snapshot-load -no-snapshot -no-boot-anim -gpu on -cores 4 -gpu swiftshader_indirect )
        emulator_params=( -no-snapshot-load -no-snapshot -no-boot-anim -gpu on -cores 4 -gpu swiftshader_indirect \
         -net-tap emu-tap-${port} -dns-server 10.10.0.25,10.10.0.26 )
    else
#        emulator_params=( -no-snapshot-load -no-snapshot -no-boot-anim -gpu on -cores 4 )
        emulator_params=( -no-snapshot-load -no-snapshot -no-boot-anim -gpu on -cores 4 \
         -net-tap emu-tap-${port} -dns-server 10.10.0.25,10.10.0.26 )
    fi
}

function complex_emu_params(){
    case "$(cat /etc/hostname)" in
            "emulator-host-2")
                emu_host_2_params
                ;;
            "emulators2")
                emu_host_2_params
                ;;
            "emulator-host1")
                emu_host_1_params
                ;;
            "emulator-host-3")
                emu_host_1_params
                ;;
            "emulators3")
                emu_host_1_params
                ;;
            "emulators4")
                emu_host_1_params
                ;;
            *)
                fail ${me} ${@}
                ;;
        esac
}

function check_port_param_passed(){
    if [[ -z ${1} ]]
    then
        echo -e "Parameter 1 must be port number on which the emulator is listening for  connections"
        fail ${me} ${@}
    fi
}

function get_pid_emu_from_port() {
    # By socket method does not work always as sometime emulators appears in stuck mode when they are not listening any of ports. So used pid search thru process list
    #pid=$( lsof -i:${1} -sTCP:LISTEN | grep IPv4 | grep qemu | awk  {'print $2'} )
    pid=$( ps aux| grep emulator${1}  | grep qemu | grep -v grep  | awk {'print$2'} )
    if [[ -z ${pid} ]]
    then
        echo -e "Emulator not running on port ${1}"
        exit 1
    else
        echo -e ${pid}
    fi
}

function kill_pid() {
    if [[ ${2} > 3 ]]
    then
        kill -9 ${1}
	fail ${@}
    else
        kill -TERM ${1}
    fi

    sleep 1

    check_pid_is_emu ${1}
    local result=${?}
    if [[ ${result} == 0 ]]
    then
        return 0
    else
        if [[ ${result} > 1 ]]
        then
            fail ${@}
        else
            # ${result} == 1
            # set -o xtrace
            kill_pid ${1} $((${2}+1))
            return ${?}
        fi
    fi
}

function check_pid_is_emu(){
# get the name of the executable so if another process is spawned with this pid shortly after killing it we don't
# accidentally think it is this process that is still running
    local ps_out
    ps_out="$(ps -p ${1})"
    if [[ ${?} == 0 ]]
    then
        # pid exists check for same name
        local exe_name=$(echo "${ps_out}" | tail -1 | awk {'print $4'})
        if [[ ${exe_name} ==  'qemu-system-x86' ]]
        then
             # pid hasn't exited yet, emulator still running
             echo -e "Waiting for emulator to stop"
             return 1
        else
            # pid was reused, emulator is stopped
            echo -e "Reused PID"
            return 0
        fi
    else
        # pid DNE, emulator is stopped
        # wrong input impossible because we can't get here without finding an emulator instance listening on the port
        return 0
    fi
    # should be unreachable
    return 99
}

function check_port_process_for_emu(){
# check if a process is listening on the correct port
    local lsof_out
    local lsof_res
    lsof_out=$(lsof -i4:${1} -sTCP:LISTEN)
    lsof_res=${?}
    if [[ ${lsof_res} != 0 ]]
    then
        if [[ ${2} > 20 ]]
        then
            return 1
        fi
        sleep 3
        check_port_process_for_emu ${1} $((${2}+1))
        return ${?}
    else
        pid=$(echo "${lsof_out}" | tail -1 | awk {'print $2'})
        local command_out
        command_out=$(ps -p ${pid} -o command | tail -1)
        local compare_out
        compare_out="qemu-system-x86_64 @emulator${1} -port $((${1}-1)) -no-snapshot-load"
        compare_out2="qemu-system-x86_64 -avd emulator${1} -port $((${1}-1)) -no-snapshot-load"
        compare_out3="qemu-system-x86_64 -debug gles @emulator${1} -no-snapshot"
        compare_out4="qemu-system-x86_64 @emulator${1} -no-snapshot-load"
        # echo -e "${command_out}"
        # echo -e "${compare_out2}"
        # echo -e "${command_out/${compare_out}}"
        # echo -e "${command_out/${compare_out2}}"
        # echo -e "${command_out/${compare_out3}}"
        if [[ "${command_out/${compare_out}}" != "${command_out}" ||\
            "${command_out/${compare_out2}}" != "${command_out}" ||\
            "${command_out/${compare_out3}}" != "${command_out}" ||\
            "${command_out/${compare_out4}}" != "${command_out}" ]]
        then
            return 0
        else
            echo -e "A different process is listening on the specified port"
            ps -p ${pid} -O user
            fail ${me} ${@}
        fi
    fi
}

function input_pin(){
    adb -s emulator-${1} shell input text 123456
}

function hit_send(){
    adb -s emulator-${1} shell input keyevent 66
}
function open_input(){
    adb -s emulator-${1} shell input keyevent 82
}

function unlock_device(){
    # set -o xtrace
    open_input ${1}
    max_ret=10
    retries=0

    # the next to lines need to be directly after each other because of the {?} used here
    check_locked_state_unlocked ${1}
    while [[ ${?} -ne 0 && ${retries} -le ${max_ret} ]]
    do
        retries=$((${retries}+1))
        # echo -e "outer while loop"
        check_screen_power_on ${1}
        while [[ ${?} -ne 0 ]]
        do
            # echo -e "inner while loop"
            open_input ${1}
            check_screen_power_on ${1}
        done
        # echo -e "inner while loop - END"
        open_input ${1}
        sleep 1
        input_pin ${1}
        sleep 1
        hit_send ${1}
        sleep 6
        check_locked_state_unlocked ${1}
    done
    # echo -e "outer while loop - END"
}

function check_screen_power_on(){
    sleep 2
    value="$(adb -s emulator-${1} shell service call power 12 | awk '{print $3}')"
    if [[ "${value}" == "00000001" ]]
    then
        # on
        # echo -e "device screen is ON"
        return 0
    else
        # off
        # echo -e "device screen is off"
        return 1
    fi
}

function check_locked_state_unlocked(){
    sleep 2
    value="$(adb -s emulator-${1} shell service call trust 8 | awk '{print $3}')"
    if [[ "${value}" == "00000000" ]]
    then
        # unlocked
        # echo -e "device is Unlocked"
        return 0
    else
        # locked
        # echo -e "device is locked"
        return 1
    fi
}

function wait_for_device(){
    local guard=1
    local counter=0
    while [[ ${guard} == 1 ]]
    do
        if [[ ${counter} -ge 65 ]]
        then
            return 1
        fi
        counter=$((${counter}+1))
        adb_out=$(adb -s emulator-${1} shell getprop init.svc.bootanim 2> /dev/null )
        if [[ ${?} == 0 && ${adb_out} == "stopped" ]]
        then
            return 0
        fi
        sleep 2
    done
}
