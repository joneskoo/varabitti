#!/usr/bin/env python
# coding: UTF-8

import sys
import os
from time import sleep
from datetime import datetime
import logging

NAME = 'varabitti'
preflist = ['eth1', 'hso0', 'ppp100', 'ppp200']
DELAY = 10
LOGFILE = '/tmp/varabitti.log'
STATEFILE = '/tmp/varabitti.state'
DEBUG = False

ifstatus = {}

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
    

def setup_logging(debug=False):
    # create logger
    logger = logging.getLogger(NAME)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    # create console handler and set level to debug
    fh = logging.FileHandler(filename=LOGFILE)
    ch = logging.StreamHandler()
    # create formatter
    formatter = logging.Formatter("%(asctime)s %(name)s[%(levelname)s]: %(message)s")
    if debug:
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info("Started")
    return logger

def write_state(ifstatus):
    f = open(STATEFILE, 'w')
    f.write("%s\t%s\n" % ('iface', 'uptime (seconds)'))
    for iface in ifstatus.keys():
        f.write("%s\t%d\n" % (iface, ifstatus[iface]*DELAY))

def main():
    curif = ''
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
                logger.info("Switched to interface %s" % (betterfound))
            else:
                logger.critical("Failed to switch interface %s" % (betterfound))
                logger.critical("Exiting...")
                sys.exit(1)
        write_state(ifstatus)
        sleep(5)

if __name__ == "__main__":
    logger = setup_logging(debug=DEBUG)
    if not DEBUG:
        child_pid = os.fork()
        if child_pid == 0:
            logger.debug("Child Process: PID# %s" % os.getpid())
        else:
            logger.debug("Parent Process: PID# %s" % os.getpid())
            sys.exit(0)
    main()
