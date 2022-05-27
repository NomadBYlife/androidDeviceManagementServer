#!/usr/bin/env bash

SCRIPT=$(readlink -f "${0}")
. "$(dirname "${SCRIPT}")/../../function_lib_dir/lib/fix_win_path.sh"
SCRIPTFILE=$(basename "${SCRIPT}")
SCRIPTPATH=$(dirname "${SCRIPT}")
LIBDIR="${SCRIPTPATH}/../../function_lib_dir/lib"
REMOTELIBDIR="${LIBDIR}/../remote_lib"

. ${LIBDIR}/run_remote_script.sh

run ${@}
