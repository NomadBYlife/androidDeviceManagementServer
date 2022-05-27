#!/usr/bin/env bash

ip=""
port=""
d_type=""
description=""
allocation=""
owner=""
enabled=""
shiftval=0

while [[ ${1} != "" ]]
do
	case ${1} in
	    "ip")
	        ip=${2}
	        shiftval+=1
	        shift 1
	        ;;
	    "port")
	        port=${2}
	        shiftval+=1
	        shift 1
	        ;;
	    "type")
	        d_type=${2}
	        shiftval+=1
	        shift 1
	        ;;
	    "description")
	        description=${2}
	        shiftval+=1
	        shift 1
	        ;;
	    "allocated")
	        allocation=${2}
	        shiftval+=1
	        shift 1
	        ;;
	    "owner")
	        owner=${2}
	        shiftval+=1
	        shift 1
	        ;;
	    "enabled")
	        enabled=${2}
	        shiftval+=1
	        shift 1
	        ;;
	    "status")
	        status=${2}
	        shiftval+=1
	        shift 1
	        ;;
	    "key")
	        key=${2}
	        shiftval+=1
	        shift 1
	        ;;
	    "priority")
	        priority=${2}
	        shiftval+=1
	        shift 1
	        ;;
		*)
		    echo "Unknown option ${1}" >&2
		    exit 98
			;;
	esac
	shiftval+=1
	shift 1
done