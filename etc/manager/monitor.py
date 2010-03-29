#!/usr/bin/env python
# coding: UTF-8
#
# Copyright Joonas Kortesalmi 2009-2010
# All rights reserved.

import sys
import os
from time import sleep, time
from datetime import datetime
import ConfigParser, os
import pickle
import logging
import signal

NAME = 'varabitti'
CONFIGFILE = '/etc/manager/monitor.conf'

class Monitor:
    def __init__(self, config):
        self.ifstatus = {}
        self.cur_if = ''
        self.read_config()

    def read_config(self):
        self.config = read_config()

    def interface_down(self, interface):
        self.ifstatus[interface] = False
        logger.debug("Interface %s is DOWN" % interface)

    def interface_pings(self, interface):
        uptime = self.interface_uptime(interface)
        logger.debug("Interface %s is UP for %0.0f seconds" % (interface, uptime))
        if self.ifstatus.get(interface, False) == False:
            self.ifstatus[interface] = time()
        
    def interface_uptime(self, interface):
        if self.ifstatus.get(interface, False):
            return time() - self.ifstatus.get(interface, False)
        else:
            return 0

    def best_interface_up(self):
        for iface in self.config['preflist']:
            if self.interface_uptime(iface):
                return iface
        return False

    def interface_is_better(self, new, previous=None):
        ''' If iface is better than current interface and has worked for at least
        treshold seconds, it is better.'''
        if self.cur_if == '':
            return True
        if previous == None:
            previous = self.cur_if
        if previous == new:
            return False
        pl = self.config['preflist']
        has_higher_pref = pl.index(new) < pl.index(previous)
        new_uptime = self.interface_uptime(new)
        prev_uptime = self.interface_uptime(previous)
        if (has_higher_pref and new_uptime > self.config['threshold']) or prev_uptime == 0:
            return True
        else:
            return False

    def switch_to_interface(self, new):
        if os.system("/etc/manager/switch.sh %s" % new) == 0:
            self.cur_if = new
            logger.info("Switched to interface %s" % new)
        else:
            logger.critical("Failed to switch interface %s" % new)

    def write_state(self):
        pickle.dump(self, open(self.config['statefile'], 'w'))

def read_config():
    c = {}
    config = ConfigParser.ConfigParser()
    config.readfp(open(CONFIGFILE))
    c['preflist'] = config.get('monitor', 'interfaces').split(" ")
    c['interval'] = config.getint('monitor', 'interval')
    c['threshold'] = config.getint('monitor', 'threshold')
    c['logfile'] = config.get('monitor', 'logfile')
    c['statefile'] = config.get('monitor', 'statefile')
    c['debug'] = config.getboolean('monitor', 'debug')
    return c

def ping(interface):
    return os.system("/etc/manager/pinger.sh " + interface) == 0


def setup_logging(config):
    # create logger
    logger = logging.getLogger(NAME)
    if config['debug']:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    # create console handler and set level to debug
    fh = logging.FileHandler(filename=config['logfile'])
    ch = logging.StreamHandler()
    # create formatter
    formatter = logging.Formatter("%(asctime)s %(name)s[%(levelname)s]: %(message)s")
    if config['debug']:
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info("Started")
    return logger


def main(config):
    try:
        m = pickle.load(open(config['statefile']))
        logger.info("Loaded previous state successfully")
        m.read_config()
    except:
        m = Monitor(config)

    preflist = m.config['preflist']
    while True:
        start = time()
        # Test each interface with ping
        for iface in preflist:
            if ping(iface):
                m.interface_pings(iface)
            else:
                m.interface_down(iface)

        # If current interface is down, switch to best working interface
        best_if = m.best_interface_up()
        current_if_up = m.interface_uptime(m.cur_if) > 0
        if not best_if == False and not m.cur_if == best_if:
            if not current_if_up:
                # Current if down, best if works
                m.switch_to_interface(best_if)
            elif m.interface_is_better(best_if):
                # New one has worked for threshold time => it is better
                m.switch_to_interface(best_if)
            else:
                logger.info("Waiting for %s to stabilize" % best_if)
        m.write_state()
        sleep_time = m.config['interval'] - (time()-start)
        if sleep_time > 0:
            sleep(sleep_time)

def restart_program(signum, frame):
    python = sys.executable
    logger.info("Restarting on SIG %s" % signum)
    os.execl(python, python, *sys.argv)

if __name__ == "__main__":
    config = read_config()
    logger = setup_logging(config)
    if not config['debug']:
        child_pid = os.fork()
        if child_pid == 0:
            logger.debug("Child Process: PID# %s" % os.getpid())
        else:
            logger.debug("Parent Process: PID# %s" % os.getpid())
            sys.exit(0)
    signal.signal(signal.SIGHUP, restart_program)
    main(config)
