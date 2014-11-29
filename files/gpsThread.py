#! /usr/bin/python

# GPS thread Parts based on / Written by;
# Dan Mandle http://dan.mandle.me September 2012
# License: GPL 2.0
# and
# http://stackoverflow.com/questions/6146131/python-gps-module-reading-latest-gps-data

import os
import gps
import time
import threading
import gammu
import re
import ConfigParser
import math
import sys
import logging

# global Vars
gpsd = None
phone = ''
boatname = ''
debug = False
# gammu statemachine
sm = None
wakeInNSecs = ''
alarmRange = ''
regularStatus = ''
sm = None
configP = None

# some hard config
logfile = '/home/pi/rpi/files/boatmon.log'
configFile = "/home/pi/rpi/files/boatmon.config"

class GpsPoller(threading.Thread):

    # class variables
    avLat = 0
    avLon = 0
    avSpeed = 0 
    avHeading = 0
    avEpx = 0
    avEpy = 0 
    numFixes = 0

    def __init__(self):

        # we are going to be a thread
        threading.Thread.__init__(self)

        # fetch the global var
        global gpsd

        # fire up the gpsd conncection
        try:
            gpsd = gps.gps("localhost", "2947")
        except:
            logging.error ('GPS thread Ops... gpsd not running right? Hint: sudo /etc/init.d/gpsd start')

        # right - set it up
        gpsd.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

        # set thread running
        #self.current_value = None
        self.running = True 
	       
    def run(self):

        # pull in the gpsd var
        global gpsd

        # some method variables
        _loop = 0
        _sumLat = 0
        _sumLon = 0
        _sumSpeed = 0
        _sumHeading = 0
        _sumEpx = 0
        _sumEpy = 0

        # while the thread is running
        while gpsp.running:

            # try and get a gpsd report
            try:
                report = gpsd.next()

                # if it looks like a fix
                if report['class'] == 'TPV':

                    # off we go
                    #if debug is True:
                        #logging.debug('GPS thread report is ' + str(report))

                    # if has the right things in the report
                    if ( hasattr(report, 'speed')
                            and hasattr(report, 'lon')
                            and hasattr(report, 'lat')
                            and hasattr(report, 'track')
                            and hasattr(report, 'epx')
                            and hasattr(report, 'epy') ):

                        # we got a good fix
                        self.numFixes += 1

                        # add each to summary
                        # and update rolling average 

                        _sumLat = _sumLat + report.lat
                        self.avLat = _sumLat / self.numFixes

                        _sumLon = _sumLon + report.lon
                        self.avLon = _sumLon / self.numFixes

                        _sumSpeed = _sumSpeed + report.speed
                        self.avSpeed = _sumSpeed / self.numFixes

                        _sumHeading = _sumHeading + report.track
                        self.avHeading = _sumHeading / self.numFixes

                        _sumEpy = _sumEpy + report.epy
                        self.avEpy = _sumEpy / self.numFixes

                        _sumEpx = _sumEpx + report.epx
                        self.avEpx = _sumEpx / self.numFixes

                        if debug is True:
                           logging.debug('GPS thread stats: LAT' + str(self.avLat) + ' LON ' +str(self.avLon) + ' VEL ' + str(self.avSpeed) + ' HEAD' + str(self.avHeading) + 'T LAT +/- ' + str(self.avEpx) + ' LON +/- ' + str(self.avEpy) + ' No fixes ' + str(self.numFixes))

            # oh it went a bit pete tong
            except StopIteration:
                gpsd = None
                logging.error('GPS thread GPSD has terminated')

    def getCurrentAvgData(self):

        # return our averaged data
        return (self.avLat, self.avLon, self.avSpeed, self.avHeading, self.avEpx, self.avEpy, self.numFixes)

    def getCurretAvgLatLon(self):

        # return just the average Lat and Lon
        return (self.avLat, self.avLon)

    def getCurrentNoFixes(self):

        # return the current number of fixes
        # so that clients can while loop till this is
        # above 10 to get a good average
        return (self.numFixes)

    def getCurrentAvgDataText(self):

        # return some nice text
        prefix = ''

        # if the number of fixes is low, pass comment
        if self.numFixes < 10:

            prefix = 'Low No. fixes '

        if int(self.avEpx) > 15 or int(self.avEpy) > 15:

            # prefix poor fix
            prefix = prefix + 'Large Lat/Lon error '

        # rounding
        roundedAvEpx = int(self.avEpx)
        roundedAvEpy = int(self.avEpy)
        roundedAvHeading = int(self.avHeading)

        # convert km/h to knots
        roundedAvSpeedKn = int(self.avSpeed / 0.539957)

        # return what we have
        return 'GPS fix: ' + prefix + 'Lat ' + str(self.avLat) + ' Lon ' + str(self.avLon) + ' ' + str(roundedAvSpeedKn) + 'KN HEAD ' +str(roundedAvHeading) + 'T Lat +/-' + str(roundedAvEpx) + 'M + Lon +/- ' + str(roundedAvEpy) + 'M Fixes ' + str(self.numFixes)

def saveConfig():

    #
    # Need to save the following...
    # configs to save
    # 'debug', 'phone', 'boatname', 'wakeInNSecs', 'lat', 'lon', 'alarmRange'

    global configP

    # all configs should have been set by loadConfig() to at least defaults
    configP.set('main', 'debug', str(debug))
    configP.set('main', 'phone', str(phone))
    configP.set('main', 'boatname', str(boatname))
    configP.set('main', 'wakeInNSecs', str(wakeInNSecs))
    configP.set('main', 'lat', str(lat))
    configP.set('main', 'lon', str(lon))
    configP.set('main', 'alarmRange', str(alarmRange))
    configP.set('main', 'regularStatus', str(regularStatus))

    logging.info(str(configP.items('main')))

    # get a filehandle and write it out
    with open(configFile, 'w') as configFilehandle:
         configP.write(configFilehandle)

def loadConfig():

    # fish out the global var
    global configP
    global debug
    global lat
    global lon
    global boatname
    global phone
    global alarmRange
    global wakeInNSecs
    global regularStatus

    # starting to read config
    if debug is True:
        logging.debug('about to read config')

    # setup the config system
    configP = ConfigParser.SafeConfigParser()
    configFileRead = configP.read(configFile)

    try:
        debug = configP.getboolean('main', 'debug')
    except:
        # default to false
        debug = False

    try:
        phone = configP.get('main', 'phone')
    except:
        # default to empty
        phone = str('')

    try:
        boatname = configP.get('main', 'boatname')
    except:
        # default to <not set>
        boatname = str('<not set>')

    try:
        wakeInNSecs = configP.getint('main', 'wakeInNSecs')
    except:
        # default to 1hr
        wakeInNSecs = int(3600)

    try:
        lat = configP.get('main', 'lat')
    except:
        # defult to 0
        lat = 0
    try:
        lon = configP.get('main', 'lon')
    except:
        # defult to 0
        lon = 0
    try:
        alarmRange = configP.getint('main', 'alarmRange')
    except:
        # defult to 0
        alarmRange = 0
    try:
        regularStatus = configP.get('main', 'regularStatus')
    except:
        # defult to 0
        regularStatus = 0

    logging.info(str(configP.items('main')))

def setUpGammu():

    # fish out the global var
    global sm

    # setups the SMS gammu system
    # returns true if all good
    # return false if there are issues

    if debug is True:
        logging.debug('About to put gammu into debug mode ...')
        gammu.SetDebugLevel('errorsdate')
        gammu.SetDebugFile(logfile)

    # create a state machine
    sm = gammu.StateMachine()

    # try and read the config
    try:
        sm.ReadConfig(Filename = '/home/pi/.gammurc')

    except Exception, e:
        logging.error('gammu Readconfig failed', e)

        # ok went bad - return false
        return False

    if debug is True:
       logging.debug('Read /home/pi/.gammurc config')

    # Now call gammu init
    # this takes about 1 sec per go, and we are going to
    # try gammuInittries times
    _gammuInittries = 5
    _tries = 1

    while True:

        # do some debug logging
        if debug is True:
            logging.debug("Trying gammu Init() %d times" % (_tries))

        try:
            if debug is True:
                logging.debug('Going to call gammu Init()')
            sm.Init()
            if debug is True:
                logging.debug('gammu Init() done')

            # we are done, so break
            break

        except Exception, e:
            loging.error('setUpGammu - sm.Init failed' , e)

        # got this far it might have failed
        _tries += 1
        time.sleep(2)

        # tried too many times
        if _tries >= _gammuInittries:

            # log summat
            logging.error('Pants tried: ' + str(_tries) + 'times to init Gammu... it broke')

            # we are not going as we can log other stuff and then exit 1 to retry
            sm = False
            return

    logging.info('Done - modem ready to read/send SMSs')
    # done
    return

def checkAnchorAlarm():

   global alarmRange
   global lat
   global lon

   if debug is True:
      logger.debug('checkAnchorAlarm')

   if alarmRange > 1:

      logger.info('checkAnchorAlarm - anchor alarm set at: ' + str(alarmRange))

if __name__ == '__main__':

    # setup logger
    try:
        logging.basicConfig(filename=logfile, level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(funcName)s %(message)s')
    except Exception, e:
        print 'Logging problem', e
        sys.exit(1)
    
    logging.info('Started ...')

    # create a gpsPollerthread and asks it to start
    gpsp = GpsPoller()
    gpsp.start()

    # load config
    loadConfig()

    # setup the modem
    setUpGammu()

    # if we have a modem configured
    # check SMS, check the anchor watch and check the regular status
#    if sm:
#        getSms()

    # check anchor alarm
    #checkAnchorAlarm()

    exit(0)

    try:
        # tell gps thread to start
        #gpsp.start()

        # while we are running ...
        while True:

            if debug is True:
                logging.debug(gpsp.getCurrentAvgDataText())

            time.sleep(2)

    # trap ctrl-c
    except (KeyboardInterrupt, SystemExit):
        logging.info('Killing gps Thread...')

        # stop the thread and wait for it to join
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing
        logging.info('Done. Exiting.')

# done
# vim:ts=4:sw=4:expandtab
# syntax on
# filetype indent plugin on
# set modeline
