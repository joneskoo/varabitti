#!/usr/bin/env python
# coding: UTF-8

import sys
import os
from time import sleep
from datetime import datetime

preflist = ['vlan20', 'vlan51', 'ppp0']
ifstatus = {'vlan20' : 0, 'vlan51' : 0, 'ppp0' : 0}
curif = ''


def ping(interface):
    return os.system("/etc/manager/pinger.sh " + interface) == 0
    

def isbetter(better, current):
    ''' If iface is better than current interface and has worked for at least
    the previous 10 times, it is better.'''
    
    if current == '': return True
    if better == current:
        return False
    higherpref = preflist.index(better) < preflist.index(current)
    betterup = ifstatus[better]
    currentdown = ifstatus[current] == 0
    if (higherpref and betterup >= 10) or currentdown:
        return True
    else:
        return False
    


while True:
    betterfound = ''
    # Ping for each interface
    for iface in preflist:
        if ping(iface):
            ifstatus[iface] += 1
            if isbetter(iface, curif) and isbetter(iface, betterfound):
                betterfound = iface
        else:
            ifstatus[iface] = 0
    # If current interface went down, use best remaining up
    if curif != '' and ifstatus[curif] == 0:
        for iface in preflist:
            if ifstatus[iface] > 0:
                betterfound = iface
                break

    # Switch to new best interface if necessary
    if betterfound != '' and curif != betterfound:
        if os.system("/etc/manager/switch.sh " + betterfound) == 0:
            curif = betterfound
            print str(datetime.now()) + ": Switched to", betterfound, ifstatus[betterfound]
        else:
            print "Failed to switch interface"
            sys.exit(1)
    sleep(15)

