#!/bin/sh

export APN="internet.saunalahti"

DEVICE=/dev/wmodem0
WANIF=hso0

TMPFIL=/tmp/hso-connect.$$

up() {
	stty 19200 -tostop
	
	rm -f $TMPFIL
	(
        /usr/sbin/chat -V -E -s -f /etc/hso/dial.chat <$DEVICE > $DEVICE
	) 2>$TMPFIL
	PIP="`grep '^_OWANDATA' $TMPFIL | cut -d, -f2`"
	NS1="`grep '^_OWANDATA' $TMPFIL | cut -d, -f4`"
	NS2="`grep '^_OWANDATA' $TMPFIL | cut -d, -f5`"

	ifconfig $WANIF $PIP pointopoint 10.6.6.6 up
    ip rule add from $PIP table 5000
    ip route add default dev $WANIF table 5000

	echo 10.6.6.6 > /etc/manager/routes/$WANIF

	(
		echo "nameserver $NS1"
		echo "nameserver $NS2"
	) > /etc/manager/resolv/resolv.conf-$WANIF

	#rm -f $TMPFIL
	
}

down() {
	/usr/sbin/chat -f /etc/hso/stop.chat <$DEVICE >$DEVICE
    for IP in `ip addr show dev hso0|awk '/inet / {print $2}'`; do
        ip rule del from $IP table 5000
    done
	/sbin/ifconfig $WANIF 0.0.0.0 down
    ip route flush table 5000 2> /dev/null
}

usage() {
	echo Usage: $0 \(up\|down\|restart\)
}

case "$1" in
	up)
		up
		;;
    plugin)
        /usr/sbin/ozerocdoff -wi 0xd055
        (sleep 10 && /etc/hso/connect.sh up )&
        ;;
	down)
		down
		;;
	restart)
		down
		up
		;;
	*)
		usage
		;;
esac

