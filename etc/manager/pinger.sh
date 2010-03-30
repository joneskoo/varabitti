#!/bin/bash

hosts="217.30.184.161 81.90.72.5 8.8.8.8"

if [ -z "$1" ]; then
	echo "Usage: $0 interface"
	exit 1
else
	interface=$1
fi

if [ "`fping -a -I $interface $hosts`" != "" ]; then
    exit 0
fi

exit 1
