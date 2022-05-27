#!/usr/bin/env bash
function run(){
#    set -o xtrace
    . "${LIBDIR}/parse_params.sh"
    user="kobil"
    . "${LIBDIR}/check_ssh.sh"

    scp -r -o "BatchMode yes" -o "StrictHostKeyChecking no" "${REMOTELIBDIR}" ${user}@${ip}:~/
    ssh -o "BatchMode yes" -o "StrictHostKeyChecking no"  ${user}@${ip} "/usr/bin/env bash -s" < "${SCRIPTPATH}/remote_script/${SCRIPTFILE}" ${port}
    script_exit=${?}
    exit ${script_exit}
}
