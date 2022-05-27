#!/usr/bin/env bash
if [[ "${SCRIPT/'C:'}" != ${SCRIPT} ]]
then
    SCRIPT="/cygdrive/c${SCRIPT/'C:'}"
fi
