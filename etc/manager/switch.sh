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
	ip route del table default default > /dev/null 2>/dev/null
	ip route add table default default dev $interface via $(cat "$PREF/routes/$interface")
	#cp -af "$PREF/resolv/resolv.conf-$interface" /etc/resolv.conf

    iptables -t mangle -F varabitti
    if [ $interface == "hso0" ]; then
        iptables -t mangle -A varabitti -j MARK --set-mark 1
    elif [ $interface == "ppp100" ]; then
        iptables -t mangle -A varabitti -j MARK --set-mark 2
    elif [ $interface == "ppp200" ]; then
        iptables -t mangle -A varabitti -j MARK --set-mark 3
    fi

    pkill -USR1 openvpn
    /etc/manager/dyndns.py
}

checkfiles
useinterface
exit 0
