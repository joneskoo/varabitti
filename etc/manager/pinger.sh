#!/bin/bash

hosts="217.30.184.161 81.90.72.5 8.8.8.8"

if [ -z "$1" ]; then
	echo "Usage: $0 interface"
	exit 1
else
	interface=$1
fi

for host in $hosts; do
	if ping -I $interface -q -c3 -W 2 -i 0.2 $host >/dev/null 2>/dev/null
	then
		exit 0
	fi
done

exit 1
