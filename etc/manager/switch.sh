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
		echo "Files missing for configuring $interface"
		exit 1
	fi
}


function useinterface () {
	route del default > /dev/null 2>/dev/null
	route add default dev $interface gw $(cat "$PREF/routes/$interface")
	cp -af "$PREF/resolv/resolv.conf-$interface" /etc/resolv.conf
	sed "s/vlan20/$interface/" /etc/netfilter.save | /sbin/iptables-restore
	ip6tables-restore < /etc/netfilter6.save
	/etc/init.d/openntpd stop >/dev/null
	ntpdate ntp.inet.fi
	/etc/init.d/openntpd start >/dev/null
	pkill -USR1 aiccu
	pkill -USR1 aiccu
	/etc/init.d/dyfi-update stop >/dev/null
	/etc/init.d/dyfi-update start >/dev/null
	/etc/init.d/tinyproxy restart >/dev/null
}

checkfiles
useinterface
