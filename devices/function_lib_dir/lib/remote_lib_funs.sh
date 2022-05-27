#!/usr/bin/env bash
function copy_remote_lib(){
scp -r -o "BatchMode yes" ${REMOTELIBDIR} ${user}@${ip}:~/
}

function clean_remote_lib() {
ssh -o "BatchMode yes" ${user}@${ip} "/usr/bin/env bash -s" << EOF
rm -rf ~/remote_lib
EOF
}