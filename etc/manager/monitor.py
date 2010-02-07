#!/usr/bin/env python
# coding: UTF-8

import sys
import os
from time import sleep
from datetime import datetime
import logging

NAME = 'varabitti'
DELAY = 5
preflist = ['eth1', 'ppp100']
ifstatus = {}
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
    
# create logger
logger = logging.getLogger(NAME)
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter("%(asctime)s %(name)s[%(levelname)s]: %(message)s")
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

logger.info("Started")
for iface in preflist:
    ifstatus[iface] = 0

while True:
    betterfound = ''
    # Ping for each interface
    for iface in preflist:
        if ping(iface):
            logger.debug("Interface %s is UP for %d seconds" % (iface, ifstatus[iface]*DELAY))
            ifstatus[iface] += 1
            if isbetter(iface, curif) and isbetter(iface, betterfound):
                betterfound = iface
        else:
            ifstatus[iface] = 0
            logger.debug("Interface %s is DOWN" % (iface))
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
            logger.info("Switched to %s %s" % (betterfound, ifstatus[betterfound]))
        else:
            logger.critical("Failed to switch interface %s" % (betterfound))
            logger.critical("Exiting...")
            sys.exit(1)
    sleep(5)

