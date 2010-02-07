#!/bin/bash

PREF=/etc/manager

if [ -n "$1" ]; then 
	interface=$1
else
	echo "usage: $0 <interface>"
	exit 1
fi

function checkfiles () {
	if [ -r "$PREF/resolv/resolv.conf-$interface" -a \
	     -r "$PREF/routes/$interface" ]; then
		return
	else
		exit 1
	fi
}


function useinterface () {
	route del default > /dev/null 2>/dev/null
	route add default dev $interface gw $(cat "$PREF/routes/$interface")
	cp -af "$PREF/resolv/resolv.conf-$interface" /etc/resolv.conf
}

checkfiles
useinterface
