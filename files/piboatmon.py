#! /usr/bin/python

# GPS thread Parts based on / Written by;
# Dan Mandle http://dan.mandle.me September 2012
# License: GPL 2.0
# and
# http://stackoverflow.com/questions/6146131/python-gps-module-reading-latest-gps-data

# mopi API stolen from:
# https://github.com/hamishcunningham/pi-tronics/blob/master/simbamon/mopiapi.py

# rounding stolen from:
# http://stackoverflow.com/questions/455612/limiting-floats-to-two-decimal-points

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
import datetime
import smbus
import errno
import RPi.GPIO
import ctypes
import requests

# global Vars
phone = ''
boatname = ''
debug = False
wakeInNSecs = ''
alarmRange = ''
alarmLat = ''
alarmLon = ''
dailyStatus = ''
lastDailyStatusCheck = ''
batteryOkMVolts = ''
sendStatus = False
logStatus = True
shutdown = False
regularStatus = False
bilgeSwitchState = None
bat1Mv = None
bat2Mv = None
presentLat = None
presentLon = None
imei = None
iteration = None
LastRunTime = None
waitedForGpsFixIterations = 0

# some object handles
gpsd = None
sm = None
configP = None
gpsp = None
mopi = None

# mopi API config
# For at least mopi firmware vX.YY...
FIRMMAJ = 3
FIRMMINR = 5

# Number of times to retry a failed I2C read/write to the MoPi
MAXTRIES = 3

# some hard config
logfile = '/home/pi/piboatmon/files/piboatmon.log'
configFile = "/home/pi/piboatmon/files/piboatmon.config"

# Code below here


class mopiapi():
        device = 0xb
        maj = 0
        minr = 0

        def __init__(self, i2cbus=-1):
                if i2cbus == -1:
                        i2cbus = self.guessI2C()
                self.bus = smbus.SMBus(i2cbus)
                [self.maj, self.minr] = self.getFirmwareVersion()
                if self.maj != FIRMMAJ or self.minr < FIRMMINR:
                        raise OSError(errno.EUNATCH, "Expected at least MoPi firmware version %i.%02i, got %i.%02i instead." % (FIRMMAJ, FIRMMINR, self.maj, self.minr))

        def getVoltage(self, input=0):
                if input == 1:
                        return self.readWord(0b00000101)  # 5
                elif input == 2:
                        return self.readWord(0b00000110)  # 6
                else:
                        return self.readWord(0b00000001)

        def setPowerOnDelay(self, poweron):
                self.writeWord(0b00000011, poweron)

        def setShutdownDelay(self, shutdown):
            self.writeWord(0b00000100, shutdown)

        def getPowerOnDelay(self):
            return self.readWord(0b00000011)

        def getFirmwareVersion(self):
            word = self.readWord(0b00001001)  # 9
            return [word >> 8, word & 0xff]

        def baseReadWord(self, register):
                tries = 0
                data = 0xFFFF
                error = 0
                while data == 0xFFFF and tries < MAXTRIES:
                        error = 0
                        try:
                                data = self.bus.read_word_data(self.device,
                                                               register)
                        except IOError as e:
                                error = e
                                time.sleep(0.33)
                        tries += 1
                # unsucessfully read
                if error != 0:
                        if e.errno == errno.EIO:
                                e.strerror = "I2C bus input/output error on read word"
                        raise e
                if data == 0xFFFF:
                        raise IOError(errno.ECOMM, "Communications protocol error on read word")
                return data

        def readWord(self, register):
                return self.baseReadWord(register)

        def writeWord(self, register, data):
                if data < 0 or data > 0xFFFF:
                        raise IOError(errno.EINVAL, "Invalid parameter, value outside range")

                # check if word is already set
                if self.readWord(register) == data:
                        return

                # try writing
                tries = 0
                error = 0
                while tries < MAXTRIES:
                        error = 0
                        try:
                                self.bus.write_word_data(self.device, register, data)
                        except IOError as e:
                                error = e
                                time.sleep(0.33)
                        # read back test
                        # slight delay to allow write to take effect
                        time.sleep(0.02)
                        if self.readWord(register) == data:
                                break
                        tries += 1
                # unsucessfully written
                if error != 0:
                        if e.errno == errno.EIO:
                                e.strerror = "I2C bus input/output error on write word"
                        raise e
                if tries == MAXTRIES:
                        raise IOError(errno.ECOMM, "Communications protocol error on write word")

        def guessI2C(self):
            # Rev2 of RPi switched the i2c address,
            # so return the right one for the board we have
            if RPi.GPIO.RPI_REVISION == 1:
                return 0
            else:
                return 1


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

        if debug is True:
            logging.debug('Setting up GpsPoller __init__ class')

        # fire up the gpsd conncection
        try:
            gpsd = gps.gps("localhost", "2947")
        except:
            logging.error('GPS thread Ops... gpsd not running right?'
                          + 'Hint: sudo /etc/init.d/gpsd start')

        # right - set it up
        gpsd.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

        # set thread running
        # self.current_value = None
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

        logging.info('Started gpsp thread')

        # while the thread is running
        while gpsp.running:

            # try and get a gpsd report
            try:
                report = gpsd.next()

                # if debug is True:
                # logging.debug('Got a gpsd report' + str(report))

                # if it looks like a fix
                if report['class'] == 'TPV':

                    # off we go
                    # if debug is True:
                        # logging.debug('GPS thread report is ' + str(report))

                    # if has the right things in the report
                    if (hasattr(report, 'speed')
                        and hasattr(report, 'lon')
                        and hasattr(report, 'lat')
                        and hasattr(report, 'track')
                        and hasattr(report, 'epx')
                        and hasattr(report, 'epy')
                       ):

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

                #       if debug is True:
                        #   logging.debug('GPS thread stats: LAT ' + str(self.avLat) + ' LON ' +str(self.avLon) + ' VEL ' + str(self.avSpeed) + ' HEAD ' + str(self.avHeading) + 'T LAT +/- ' + str(self.avEpx) + ' LON +/- ' + str(self.avEpy) + ' No. fixes ' + str(self.numFixes))

            # oh it went a bit pete tong
            except StopIteration:
                gpsd = None
                logging.error('GPS thread GPSD has terminated')

    def getCurrentAvgData(self):

        # return our averaged data
        return (self.avLat, self.avLon, self.avSpeed, self.avHeading,
                self.avEpx, self.avEpy, self.numFixes)

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

        if self.numFixes == 0:
            # No GPS fix (yet)
            return 'NO GPS FIX!'

        # rounding
        roundedAvEpx = int(self.avEpx)
        roundedAvEpy = int(self.avEpy)
        roundedAvHeading = int(self.avHeading)

        # find the biggest EP error and report on that
        roundedEp = max(roundedAvEpx, roundedAvEpy)

        # if the number of fixes is low, or EP low
        if self.numFixes < 10 or roundedEp > 15:

            # prefix poor fix
            prefix = prefix + 'POOR '

            if debug is True:
                logging.debug('numFixes: ' + str(self.numFixes)
                              + ' roundedEp: ' + str(roundedEp))

        # convert km/h to knots
        roundedAvSpeedKn = int(self.avSpeed / 0.539957)

        # return what we have
        return 'GPS fix: ' + prefix + 'Lat ' + "{0:.6f}".format(self.avLat) \
               + ' Lon ' + "{0:.6f}".format(self.avLon) + ' ' \
               + str(roundedAvSpeedKn) + 'KN ' + str(roundedAvHeading) \
               + 'T EP +/-' + str(roundedEp)


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
    configP.set('main', 'alarmLat', str(alarmLat))
    configP.set('main', 'alarmLon', str(alarmLon))
    configP.set('main', 'alarmRange', str(alarmRange))
    configP.set('main', 'dailyStatus', str(dailyStatus))
    configP.set('main', 'lastDailyStatusCheck', str(lastDailyStatusCheck))
    configP.set('main', 'batteryOkMVolts', str(batteryOkMVolts))
    configP.set('main', 'sendStatus', str(sendStatus))
    configP.set('main', 'regularStatus', str(regularStatus))
    configP.set('main', 'iteration', str(iteration))
    configP.set('main', 'LastRunTime', str(LastRunTime))

    logging.info(str(configP.items('main')))

    # get a filehandle and write it out
    with open(configFile, 'w') as configFilehandle:
        configP.write(configFilehandle)

    # now be nice and flush
    # http://stackoverflow.com/questions/15983272/does-python-have-sync
    libc = ctypes.CDLL("libc.so.6")
    libc.sync()


def loadConfig():

    # fish out the global var
    global configP
    global debug
    global alarmLat
    global alarmLon
    global boatname
    global phone
    global alarmRange
    global wakeInNSecs
    global dailyStatus
    global lastDailyStatusCheck
    global batteryOkMVolts
    global sendStatus
    global regularStatus
    global iteration
    global LastRunTime

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
        regularStatus = configP.getboolean('main', 'regularStatus')
    except:
        regularStatus = False

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
        alarmLat = configP.get('main', 'alarmLat')
    except:
        # defult to ''
        alarmLat = ''
    try:
        alarmLon = configP.get('main', 'alarmLon')
    except:
        # defult to ''
        alarmLon = ''
    try:
        alarmRange = configP.getint('main', 'alarmRange')
    except:
        # defult to ''
        alarmRange = ''
    try:
        dailyStatus = configP.get('main', 'dailyStatus')
    except:
        # defult to ''
        dailyStatus = ''
    try:
        lastDailyStatusCheck = configP.get('main', 'lastDailyStatusCheck')
    except:
        lastDailyStatusCheck = ''

    try:
        batteryOkMVolts = configP.get('main', 'batteryOkVolts')
    except:
        batteryOkMVolts = 1100

    try:
        sendStatus = configP.getboolean('main', 'sendStatus')
    except:
        sendStatus = False

    try:
        iteration = configP.getint('main', 'iteration')
    except:
        iteration = 0

    try:
        batteryOkMVolts = configP.get('main', 'LastRunTime')
    except:
        batteryOkMVolts = 0

    logging.info(str(configP.items('main')))


def setUpGammu():

    # fish out the global var
    global sm
    global imei

    # setups the SMS gammu system
    # returns true if all good
    # return false if there are issues

    if debug is True:
        logging.debug('About to put gammu into debug mode logging to: '
                      + str(logfile))
        gammu.SetDebugLevel('errorsdate')
        gammu.SetDebugFile(logfile)

    # create a state machine
    sm = gammu.StateMachine()

    # try and read the config
    try:
        sm.ReadConfig(Filename='/home/pi/.gammurc')

    except Exception, e:
        logging.error('gammu Readconfig failed' + str(e))
        sm = None
        return

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
            logging.error('setUpGammu - sm.Init failed' + str(e))
            sm = None
            return

        # got this far it might have failed
        _tries += 1
        time.sleep(2)

        # tried too many times
        if _tries >= _gammuInittries:

            # log summat
            logging.error('Pants tried: ' + str(_tries)
                          + 'times to init Gammu... it broke')

            # we keep going as we can log other stuff and then exit 1 to retry
            sm = False
            return
    try:
        imei = sm.GetIMEI()
    except Exception, e:
        logging.error('failed to sm.GetIMEI(): ' + str(e))
        imei = 0

    logging.info('Done - modem imei: ' + str(imei)
                 + ' ready to read/send SMSs')
    # done
    return


def checkAnchorAlarm():

    global alarmRange
    global alarmLat
    global alarmLon
    global gpsp
    global sm

    if debug is True:
        logging.debug('alarmRange is: ' + str(alarmRange) + ' alarmLat: '
                      + str(alarmLat) + ' alarmLon: ' + str(alarmLon))

    if alarmRange > 1:

        # check we have a lat/lon to compare to
        if alarmLat != '' and alarmLon != '':

            # if we have a lat/lon to compare to
            # get fix, wait for 15 tries

            _loop = 0
            while gpsp.getCurrentNoFixes() < 10:
                # loop till we get 10 fixes... should not be long
                time.sleep(1)
                if debug is True:
                    logging.debug('Not enough gps fixes - we want 10 - '
                                  + 'gpsp.getCurrentNoFixes() is: '
                                  + str(gpsp.getCurrentNoFixes())
                                  + ', we have looped: ' + str(_loop))
                _loop += 1

                if _loop == 15:
                    logging.error('Not enough GPS fixes, tried: '
                                  + str(_loop) + ' times')
                    break

            # fetch a fix, may / may not be good
            newlat, newlon = gpsp.getCurretAvgLatLon()

            if newlat is 0 or newlon is 0:

                # got an empty fix
                _txt = 'No present position fix to compare to set anchor ' \
                       + 'alarm - alarm range is: ' + str(alarmRange) \
                       + ' alarm Lat: ' + str(alarmLat) \
                       + ' alarm Lon: ' + str(alarmLon)

                # log the error, send an SMS and return
                logging.error(_txt)
                sendSms(phone, _txt)
                return

            if debug is True:
                logging.debug('Present lat: ' + str(newlat) + ' lon: '
                              + str(newlon))

            # compare fix with saved config
            movedDistanceKm = distance(float(alarmLat), float(alarmLon),
                                       float(newlat), float(newlon))
            # change the distance to meters rounded (not 100% accurate)
            movedDistanceM = int(movedDistanceKm * 1000)

            if debug is True:
                logging.debug('Distance moved is: ' + str(movedDistanceM))

            # work out if less than alarmRange
            if movedDistanceM > alarmRange:

                if debug is True:
                    logging.info('Moved distance: ' + str(movedDistanceM)
                                 + 'M is more than alarmRange: '
                                 + str(alarmRange) + 'M')

                txt = 'ANCHOR ALARM.  Distance moved: ' + str(movedDistanceM) \
                      + 'M, Alarm Range: ' + str(alarmRange) \
                      + 'M. New position - Lat: ' + str(newlat) \
                      + ', Lon: ' + str(newlon)

                txt2 = 'ANCHOR ALARM: http://maps.google.com/maps' \
                       + '?z=12&t=m&q=loc:' + str(newlat) + '+' + str(newlon)

                if sm != '' and phone != '':

                    # send both texts
                    sendSms(phone, txt)
                    sendSms(phone, txt2)

                else:
                    logging.error('No SMS statemachine, or phone configured'
                                  + ' - cannot send anchor alarm SMS')

            else:
                # we have moved less than the alarm
                logging.info('We have moved: ' + str(movedDistanceM)
                             + 'M, which is not enough to setoff alarm: '
                             + str(alarmRange) + 'M')

        else:
            # lat / lon are empty !!!!
            logging.error('Anchor alarm set: ' + str(alarmRange)
                          + ' , but Lat or Lon are empty')
    else:
        # No anchor alarm ... bale
        logging.info('No Anchor alarm set')


def sendSms(_number, _txt):

    # send the message to the phone
    # trap any nonesense

    if _number is '':
        # no number so use global phone
        _number = phone

    if _number is '':
        logging.error('Trying to send a SMS to a phone that is not set'
                      + ' - phone: ' + str(_number))
        # give up
        return False

    if _txt is '':
        logging.error('trying to send an empty SMS?')
        return False

    # Prefix with boatname and time
    # and add iteration to the end
    _txt = datetime.datetime.now().strftime("%a %X") + ' ' + boatname \
        + ': ' + _txt + ', ' + str(iteration)

    if debug is True:
        logging.debug('Trying to send SMS message: ' + str(_txt)
                      + ' to: ' + str(_number))

    # go for it
    message = {'Text': _txt, 'SMSC': {'Location': 1}, 'Number': _number}

    try:

        if debug is True:
            logging.debug('About to try sm.SendSMS(message)')

        sm.SendSMS(message)
        logging.info('Message sent to: ' + str(_number))

        # yay it worked!!!!
        return True

    except Exception, e:

        # Ops...
        logging.error('Exception: ' + str(e))
        return False


def distance(lat1, lon1, lat2, lon2):

    # stolen from;
    # https://github.com/sivel/speedtest-cli/blob/master/speedtest_cli.py
    # Determine distance between 2 sets of [lat,lon] in km
    # aka Great Circle distance use a spherical model and can be out up to 0.5%
    # which on 100M is 50cm... hardly significant on a boat.
    # https://en.wikipedia.org/wiki/Great-circle_distance

    # assume a round earth ...
    # radius = 6371  # km
    # more accurate wikipedia number?
    # http://en.wikipedia.org/wiki/Decimal_degrees
    # radius = 6378.169
    # Geopi numbers - average great cicle
    # https://github.com/geopy/geopy/blob/master/geopy/distance.py
    radius = 6372.795

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2)) * math.sin(dlon / 2)
         * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d


def getSms():

    global sm
    sms = []
    _status = None
    _remain = 0
    _start = True
    cursms = None
    gotSMS = 0

    if debug is True:
        logging.debug('About to get sm.GetSMSStatus()')

    try:
        _status = sm.GetSMSStatus()

    except Exception, e:
        logging.error('Failed sm.GetSMSStatus() ' + str(e))

    _remain = _status['SIMUsed'] + _status['PhoneUsed']
    + _status['TemplatesUsed']

    logging.info(str(_remain) + ' SMS(s) to deal with')

    if _remain == 0:
        return

    while _remain > 0:

        if _start:

            cursms = sm.GetNextSMS(Start=True, Folder=0)
            if debug is True:
                logging.debug('In start processing SMS: ' + str(cursms))

            # we got some to deal with
            _start = False
            processSMS(cursms)
            gotSMS += 1

        else:

            if debug is True:
                logging.debug('In else processing SMS: ' + str(cursms))

            cursms = sm.GetNextSMS(Start=True, Folder=0)
            processSMS(cursms)
            gotSMS += 1

        # delete the SMS
        for x in range(len(cursms)):
            logging.info('Deleting SMS no: ' + str(x))
            if debug is True:
                logging.debug('About to delete SMS in location: '
                              + str(cursms[x]['Location']))
            sm.DeleteSMS(cursms[x]['Folder'], cursms[x]['Location'])

        _remain = _remain - len(cursms)
        sms.append(cursms)


def processSMS(sms):

    # lower text the message so we can parse it
    # anoying the iPhone capitalising first char
    _txt = sms[0]['Text']

    # trap any uuencode - thx Giffgaff!!!
    _txt = _txt.encode('ascii', 'ignore')

    _lowertxt = _txt.lower()
    _understoodSms = False

    # as we might set it grab it
    global sendStatus

    if 'set debug' in _lowertxt:
        debugSms(sms)
        _understoodSms = True

    if 'set regular status' in _lowertxt:
        regularStatusSms(sms)
        _understoodSms = True

    if 'setup' in _lowertxt:
        setupSms(sms)
        _understoodSms = True

    # might be a phone set command
    if 'set phone' in _lowertxt:
        updatePhoneSms(sms)
        _understoodSms = True

    # set the anchor alarm
    if 'set anchor alarm' in _lowertxt:
        setAnchorAlarmSms(sms)
        _understoodSms = True

    # might be a set daily status
    if 'set daily status' in _lowertxt:
        setDailyStatusSms(sms)
        _understoodSms = True

    # might be a config txt to set the battery mV
    if 'set battery ok mvolts' in _lowertxt:
        setBatteryOkMVoltsSms(sms)
        _understoodSms = True

    if 'set sleep time' in _lowertxt:
        setWakeInNSecsSms(sms)
        _understoodSms = True

    # or we might be switching dailystatus off
    if 'set daily status off' in _lowertxt:
        dailyStatusOffSms(sms)
        _understoodSms = True

    # send instructions SMS
    if 'send instructions' in _lowertxt:
        sendInstructionsSms(sms)
        _understoodSms = True

    # send a status txt
    if 'send status' in _lowertxt:
        # fire at least a statusTxt or dailyStatus to avoid 2 SMS
        sendStatus = True
        _understoodSms = True

    if 'set boatname' in _lowertxt:
        setBoatnameSms(sms)
        _understoodSms = True

    if 'shutdown' in _lowertxt:
        shutdownSms(sms)
        _understoodSms = True

    # no idea what the SMS is...
    if _understoodSms is False:

        logging.info('Could not parse SMS message: ' + str(_txt))

    # finished


def regularStatusSms(sms):

    # either put regularStatus on/off
    _lowertxt = sms[0]['Text'].lower()

    reply = None

    # set global var
    global regularStatus

    if debug is True:
        logging.debug('Message to parse is: ' + str(sms[0]['Text']))

    if 'set regular status on' in _lowertxt:

        _mins = wakeInNSecs / 60

        if regularStatus is True:
            reply = 'regularStatus is already True, keeping it.  You will get' \
                    + ' SMS status messages approx.  every' + str(_mins) \
                    + ' minutes.'

        else:

            reply = 'Regular status being set to True,' \
                    + ' you will get SMS status' \
                    + ' messages approx. every' + str(_mins) + ' minutes.'

            regularStatus = True
            saveConfig()

    elif 'set regular status off' in _lowertxt:

        if regularStatus is True:

            reply = 'regularStatus being turned off'
            regularStatus = False
            saveConfig()

        else:

            reply = 'regularStatus already off'
    else:

        # could not parse sms
        reply = 'Could not parse: ' + str(sms[0]['Text'])

    # got this far ... log reply, send SMS reponse
    logging.info(reply)
    sendSms(phone, reply)


def setupSms(sms):

    # try for a long time to get a GPS fix and report OK if true
    # otherwise reply that we could not - and re-run and check GPS

    # fish out the global
    global phone

    _lowertxt = sms[0]['Text'].lower()
    number = str(sms[0]['Number'])

    reply = None

    if debug is True:
        logging.debug('Running setup ...')

    _loop = 0
    while gpsp.getCurrentNoFixes() < 1:
        # loop till we get a fixes... or exit should not be long

        if debug is True:
            logging.debug('Not gps fixs, we have looped: ' + str(_loop))

        # up loop counter
        _loop += 1

        if _loop == 45:

            # we got this far ... ops
            # create a reply, log it, and break

            reply = 'Timed out getting GPS Fix whilst running setup.' \
                    + '  We tried: ' + str(_loop) \
                    + ' times.  Please check GPS anntena/connections'
            logging.error(reply)

            break

        # wait a bit
        time.sleep(1)

    if gpsp.getCurrentNoFixes() > 1:

        # we got one fix... yay!
        phone = number
        saveConfig()

        reply = 'Setup: GPS got: ' + str(gpsp.getCurrentNoFixes()) \
                + ' fix(s).  Also setting the phone number to this number: ' \
                + str(phone)
        logging.info(reply)

    # we should have a reply eitherway ...
    sendSms(number, reply)


def shutdownSms(sms):

    # this should only work from the registered phone number
    # otherwise barf out and SMS

    number = str(sms[0]['Number'])
    reply = None

    # fish out the global
    global shutdown

    if number == phone:
        reply = 'Recieved shutdown command from phone: ' + str(phone) \
                + ', will shutdown and not wake up!!! Will need to be' \
                + '  manually restarted'

        logging.info(reply)
        shutdown = True

    else:
        # else not from registered number
        reply = 'Recieved shutdown command from: ' + str(number) \
                + ', which is not registered phone: ' + str(phone) \
                + ', ignoring'

        logging.info(reply)

    # sent the SMS
    sendSms(phone, reply)


def setWakeInNSecsSms(sms):

    # get the number
    number = str(sms[0]['Number'])
    _txt = sms[0]['Text']
    _lowertxt = _txt.lower()
    reply = None
    _mins = 0

    # fish out the global var
    global wakeInNSecs

    results = re.search("set sleep time (\d+)", _lowertxt)

    if debug is True:
        logging.debug('text is: ' + str(_txt))

    # if we have a match
    if results:

        _mins = results.group(1)

        if debug is True:
            logging.debug('Mins is : ' + str(_mins))

        wakeInNSecs = int(_mins) * 60

        # round it up
        _mins = wakeInNSecs / 60

        # save the config for next checks
        saveConfig()
        # reply
        reply = 'Sleep time set to: ' + str(_mins) + ' minutes'
        logging.info(reply)

    # could not parse results
    else:
        reply = 'Could not set sleep time: ' + str(_txt)
        logging.error(reply)

    # sent the SMS
    sendSms(number, reply)


def setBatteryOkMVoltsSms(sms):

    # get the number
    number = str(sms[0]['Number'])
    _txt = sms[0]['Text']
    _lowertxt = _txt.lower()
    reply = None

    # fish out the global var
    global batteryOkMVolts

    results = re.search("set battery ok mvolts (\d{5})", _lowertxt)

    # if we have a match
    if results:

        batteryOkMVolts = results.group(1)

        # save the config for next checks
        saveConfig()
        # reply
        reply = 'Battery OK mvolts set to: ' + str(batteryOkMVolts) + ' mV'
        logging.info(reply)

    # could not parse results
    else:
        reply = 'Could not set battery ok mvolts: ' + str(_txt) \
                + '. Must be in 5 digits long e.g. 13000'
        logging.error(reply)

    # sent the SMS
    sendSms(number, reply)


def setDailyStatusSms(sms):

    # get the number
    number = str(sms[0]['Number'])
    _txt = sms[0]['Text']
    _lowertxt = _txt.lower()
    reply = None

    # fish out the global var
    global dailyStatus

    results = re.search("set daily status (\d{4})", _lowertxt)

    # if we have a match
    if results:

        dailyStatus = results.group(1)

        # save the config for next checks
        saveConfig()

        # reply
        reply = 'Daily status setup to be sent around: ' \
                + str(dailyStatus) + ' UTC each day (depends on wakeUp)'
        logging.info(reply)

    # could not parse results
    else:
        reply = 'Could not parse new daily status update: ' \
                + str(_txt) + 'Needs to be 4 digit 24hr clock notation'
        logging.error(reply)

    # sent the SMS
    sendSms(number, reply)


def setBoatnameSms(sms):

    # get the number
    number = str(sms[0]['Number'])
    _txt = sms[0]['Text']
    _lowertxt = _txt.lower()
    reply = None

    # fish out the global
    global boatname

    if 'set boatname' in _lowertxt:

        # setup regex
        results = re.search('boatname (.+)$', _txt)

        # check it matched...
        if results:

            # fish out the first group
            boatname = results.group(1)

            # and if it is not null change config and send sms
            if boatname:

                reply = 'Setting boatname to: ' + str(boatname)
                logging.info(reply)

            else:
                reply = 'Could not parse: ' + str(_txt) + ' to set boatname'
                logging.error(reply)

        else:
            # got confused
            reply = 'Could not parse: ' + str(_txt) + ' to set boatname'
            logging.error(reply)
            sendSms(number, reply)

        # sent the SMS
        sendSms(number, reply)
        return


def setPowerOnDelay():

    # fish out the global object
    global mopi
    global wakeInNSecs
    global shutdown

    # set the PowerOnDelay to wak
    if wakeInNSecs < 60:
        logging.error(str(wakeInNSecs) + ' below 60 secs, '
                      + 'setting to 60 min...')
        wakeInNSecs = 60

    if shutdown is True:
        wakeInNSecs = 0

        if debug is True:
            logging.debug('shutdown is true, so setting'
                          + ' wakeInNSecs to 0 to never wake up')

    logging.info('Setting mopi mopi.setPowerOnDelay to: ' + str(wakeInNSecs))

    mopi.setPowerOnDelay(wakeInNSecs)

    print 'Setting wake on delay to: ' + str(wakeInNSecs)


def getInputmV():

    global bat1Mv
    global bat2Mv

    bat1Mv = float(mopi.getVoltage(1))
    bat2Mv = float(mopi.getVoltage(2))


def getBatteryText():

    status = ''

    global bat1Mv
    global bat2Mv

    # get battery volts from mopi
    getInputmV()

    if debug is True:
        logging.debug('bat1Mv is: ' + str(bat1Mv) + ' mv bat2Mv is: '
                      + str(bat2Mv) + ' mv')

    # for each battery define a state
    # above 13000 charging
    # above 11000 ok
    # lower than 11000 low
    # 0 == missing/dead
    # below
    # "{0:.2f}".format((bat1Mv) / 1000)
    if bat1Mv > 13000:
        status = status + 'Bat1 Charging: ' \
            + "{0:.2f}".format((bat1Mv) / 1000) + 'V'
    elif bat1Mv > batteryOkMVolts:
        status = status + 'Bat1 OK: ' + "{0:.2f}".format((bat1Mv) / 1000) + 'V'
    elif bat1Mv == 0:
        status = status + 'Bat1 Missing: 0V'
    elif bat1Mv < 11000:
        status = status + 'Bat1 Low: ' \
            + "{0:.2f}".format((bat1Mv) / 1000) + 'V'
    else:
        status = status + 'Bat1 state unkown'

    # Battery2 is assumed to be a 9v
    # above 9000 is Ok
    # below 5200 is low
    # 0 == mising/dead
    if bat2Mv > 7000:
        status = status + ' Bat2 OK: ' \
            + "{0:.2f}".format((bat2Mv) / 1000) + 'V'
    elif bat2Mv == 0:
        status = status + ' Bat2 Missing: 0V'
    elif bat2Mv < 5200:
        status = status + ' Bat2 Low: ' \
            + "{0:.2f}".format((bat2Mv) / 1000) + 'V'
    else:
        status = status + 'Bat2 state unkown'

    return status


def checkBattery():

    # get battery volts from mopi
    getInputmV()

    if bat2Mv > batteryOkMVolts and bat2Mv > 5200:
        return True
    else:
        return False


def checkBilgeText():

    if bilgeSwitchState is True:
        status = 'BILGE ALARM !!!'
    elif bilgeSwitchState is None:
        status = 'BILGE Unkown'
    else:
        status = 'BILGE OK'

    logging.info(status)

    return status


def checkBilge():

    # checks switch and bleats if not ok

    if bilgeSwitchState is True:

        if debug is True:
            logging.debug('bilgeSwitchState is true ... '
                          + 'about to try to send SMS')

        # oh pants!!!
        # try and send the SMS
        sendSms(phone, checkBilgeText())


def getStatusText():

    # build a status string
    status = getBatteryText() + ' ' + checkBilgeText() + ' ' \
        + gpsp.getCurrentAvgDataText()

    if bilgeSwitchState is False and checkBattery() is True:
        status = 'OK\n' + status

    else:

        if debug is True:
            logging.debug('bilgeSwitchState is ' + str(bilgeSwitchState)
                          + ' and checkBattery() is: ' + str(checkBattery()))
        status = 'NOT OK\n' + status

    return status


def setAnchorAlarmSms(sms):

    # lower case the message
    _lowertxt = sms[0]['Text'].lower()

    # get the number
    number = str(sms[0]['Number'])
    reply = None
    _newRange = None

    # fish out the global
    global alarmRange
    global alarmLat
    global alarmLon

    # lookfing for string like
    # set anchor alarm 100m
    # set anchor alarm
    # set anchor alarm off

    # deal with an off first
    if 'set anchor alarm off' in _lowertxt:

        logging.info('Disabling the Anchor Alarm')
        # disabled the Alarm by Nulling the values
        alarmLat = ''
        alarmLon = ''
        alarmRange = ''

        # sort a message to send back
        reply = 'Anchor alarm being diabled!'

        # sent the SMS
        sendSms(number, reply)

        # done - return
        return

    # got this far assume it is a set anchor alarm on

    # parse the SMS for alarm range
    results = re.search("set anchor alarm (\d+)", _lowertxt)
    if results:

        _newRange = results.group(1)
        if debug is True:
            logging.debug('Found the following regex results: '
                          + str(_newRange))

        if _newRange > 10:

            # so should have something sensible to set the alarmRange to
            # make it an int for sanity...
            alarmRange = int(_newRange)

        else:

            # less than 10
            reply = 'New Anchor Alarm appears to be less than 10M ... ' \
                    + 'please try again (with a higher number)'
            loggin.info(reply)
            sendSms(number, reply)
            return

    else:
        # not re match set 20M as default
        alarmRange = 20

    # so we should have something sensible by now ..
    _presentLat, _presentLon = gpsp.getCurretAvgLatLon()

    if _presentLat is '' or _presentLon is '':

        reply = 'Trying to set Anchor Alarm, but Present Lat is: ' \
                + str(_presentLat) + ' or Lon is: ' + str(_presentLon) \
                + ' ie we have no fix to alarm from!!!'

        logging.error(reply)

    else:
        # ok we got this far ... should be good
        reply = 'Anchor Alarm being set for Lat: ' + str(_presentLat) \
                + ' Lon: ' + str(_presentLon) + ' Alarm range: ' \
                + str(alarmRange)

        alarmLat = _presentLat
        alarmLon = _presentLon
        logging.info(reply)

    # send replry
    sendSms(number, reply)


def updatePhoneSms(sms):

    # lower case the message
    _lowertxt = sms[0]['Text'].lower()
    # get the number
    number = str(sms[0]['Number'])
    reply = None
    _newPhone = None

    global phone

    # lookfing for string like
    # update phone NNNNN

    # parse the SMS for a phone number like
    # 07788888888
    # +0452345234

    if debug is True:
        logging.debug('update phone message is: ' + str(sms[0]['Text']))

    _newPhoneRegEx = re.search("set phone (\+*\d+)", _lowertxt)

    if _newPhoneRegEx is None:

        reply = 'Could not parse: ' + str(str(sms[0]['Text']))
        logging.info(reply)
        sendSms(number, reply)
        return

    _newPhone = _newPhoneRegEx.group(1)

    if _newPhone is not '':

        if debug is True:
            logging.debug('Found new phone number: ' + str(_newPhone))

        # keep the old phone
        oldphone = phone
        phone = _newPhone

        # got this far, should have something sensible to set
        logging.info('Changing phone from: ' + str(oldphone) + ' to: '
                     + str(_newPhone))

        if oldphone != '':
            # sort a message to reply back letting original phone know of reset
            reply = ': New phone being set: ' + str(phone) \
                    + '.  To reset the phone back to this phone, ' \
                    + ' reply to this SMS with:\n\nupdate phone ' \
                    + str(oldphone)

            # sent the reply SMS
            sendSms(oldphone, reply)

        # reply to _newphone
        reply = 'New phone being set to: ' + str(phone)
        sendSms(phone, reply)

    else:
        logging.error('Not a phone number we could parse in: '
                      + str(sms[0]['Text']))


def debugSms(sms):

    # either put debug on/off
    _lowertxt = sms[0]['Text'].lower()
    number = str(sms[0]['Number'])

    reply = None

    # set global var
    global debug

    if debug is True:
        logging.debug('Message to parse is: ' + str(sms[0]['Text']))

    if 'set debug on' in _lowertxt:

        if debug is True:
            reply = 'debug already set to true - keeping it on'

        else:
            reply = 'debug was off - being set to true'

        debug = True
        logging.info(reply)

    elif 'set debug off' in _lowertxt:

        if debug is True:
            reply = 'debug was on - setting to off'

        else:
            reply = ' debug already off - keeping it off'

        logging.info(reply)
        debug = False

    else:
        logging.info('No idea what that txt was...')
        reply = 'Could not parse debug message : ' + _lowertxt

    sendSms(number, reply)


def sendInstructionsSms(sms):

    # get the number
    number = str(sms[0]['Number'])

    # Put are reply together
    reply = "set then\nphone NUM\ndaily status [TIME|off]\n" \
            + "set anchor alarm [M|off]\ndebug [on|off]\n" \
            + "battery ok volts\nsleep time MINS\nsend state\n" \
            + "set battery ok mvolts [mvolts]shutdown\n"

    logging.info('Sending instructions SMS')

    # sent the SMS
    sendSms(number, reply)


def checkLogStatus():

    if logStatus is True:
        # log status
        logging.info(getStatusText())
    elif debug is True:
        logging.debug('called, but already run as logStatus is: '
                      + str(logStatus))


def checkRegularStatus():

    # fish out the global
    global sendStatus

    if debug is True:
        logging.debug('regularStatus is: ' + str(regularStatus)
                      + ',sendStatus is: ' + str(sendStatus))

    # check if we need to send regular Status
    if regularStatus is True:

        sendStatus = True
        logging.info('regularStatus is: ' + str(regularStatus)
                     + ', therefore we are going to send status this run'
                     + ', by setting sendStatus to: ' + str(sendStatus))


def checkDailyStatus():

    # if dailyStatus is not set bale
    if dailyStatus == '':
        logging.info('No dailyStatus check set')
        return

    # we might set this if we run
    global lastDailyStatusCheck
    global sendStatus

    # check that have not sent a status message in timeframe

    # what is the time now?
    _now = datetime.datetime.now()

    # some defaults
    _minute = 0
    _hour = 0
    _nextAlarm = None

    # have we run today - note if this is blank it will run

    try:
        _lastRun = datetime.datetime.strptime(lastDailyStatusCheck,
                                              "%Y-%m-%d %H:%M:%S.%f")

        if _lastRun.date() == _now.date():

            # we ran today ... exit
            logging.info('Ran today already: ' + str(_lastRun))

            return

    except ValueError:
        _lastRun = None
        logging.error('lastDailyStatusCheck: ' + str(lastDailyStatusCheck)
                      + 'Could not be parsed into a date')

    # so ... if we got this far we need to check the time

    # split dailyStatus into hours / minutes
    p = re.compile('..')

    try:
        _hour, _minute = p.findall(str(dailyStatus))
    except ValueError:
        logging.error('Could not parse dailyStatus: ' + str(dailyStatus)
                      + ' into _hour, _minute')

    # http://www.saltycrane.com/blog/2008/06/how-to-get-current-date-and-time-in/
    if _hour >= 0 and _minute >= 0:
        _nextAlarm = datetime.datetime(_now.year, _now.month, _now.day,
                                       int(_hour), int(_minute), 0)
        logging.info('Next daily check due: ' + str(_nextAlarm))

    else:
        logging.error('Cannot split dailyStatus into _hour / _min: '
                      + str(dailyStatus))
        # as we have nothing to compare, assume we need to run

    if _now > _nextAlarm:

        if debug is True:
            logging.debug('alarm fired')

        # alarm fired, so therefore send status
        sendStatus = True

        if sendAndLogStatus() is True:

            # clear any sendStatus flag
            # save config to preserve fact we ran in lastDailyStatusCheck
            sendStatus = False
            lastDailyStatusCheck = _now

            logging.info('Daily SMS sent, lastDailyStatusCheck updated to: '
                         + str(lastDailyStatusCheck))

        else:
            # log the fact we ops'ed
            logging.error('Failed to send daily SMS'
                          + ' - should try again next run')


def sendAndLogStatus():

    # sends a status message - either add hoc or daily
    # check to see if we need to send a status message
    # ie failed, or each time we run

    # fish out the global
    global sendStatus
    global logStatus

    _sent = False

    if debug is True:
        logging.debug('sendStatus is: ' + str(sendStatus)
                      + ', logStatus is: ' + str(logStatus))

    if sendStatus is True:

        # get some text
        message = getStatusText()
        logging.info(str(message))

        # clear the flag
        logStatus = False

        if debug is True:
            logging.debug('About to call sendSMS as sendStatus is: '
                          + str(sendStatus))

        if sendSms(phone, message):
            # went ok - clear any flags
            sendStatus = False
            _sent = True
        else:
            logging.error('Failed to send status ... will try next run'
                          + ' as sendStatus is: ' + str(sendStatus))
            sendStatus = True

    return _sent


def setBilgeSwitchState():

    # set bilgeSwitchState  on the state of the bilge switch
    # false means ON so inverse these in the if statement

    global bilgeSwitchState

    if debug is True:
        logging.debug('Setting up RPi.GPIO pins')

    # from http://razzpisampler.oreilly.com/ch07.html
    RPi.GPIO.setmode(RPi.GPIO.BCM)
    RPi.GPIO.setup(18, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)

    _input18State = RPi.GPIO.input(18)

    if _input18State is False:

        # BilgeSwitch is on ... Ops:

        message = 'Bilge Switch is ON !!!'
        logging.info(message)

        bilgeSwitchState = True

    else:

        bilgeSwitchState = False
        logging.info('Bilge Swich is off')

    return bilgeSwitchState


def sendHttpsLogging():

    # send an HTTPS get request with status messages as query string
    # Using HTTPS as it is the lowest common denominator

    # get uptime
    runtime = uptimeSecs()

    payload = {'wakeInNSecs': str(wakeInNSecs),
               'runtime': str(runtime),
               'BilgeSwitchState': str(bilgeSwitchState),
               'phone': str(phone),
               'boatname': str(boatname),
               'alarmRange': str(alarmRange),
               'alarmLat': str(alarmLat),
               'alarmLon': str(alarmLon),
               'lastDailyStatusCheck': str(lastDailyStatusCheck),
               'shutdown': str(shutdown),
               'batteryOkMVolts': str(batteryOkMVolts),
               'regularStatus': str(regularStatus),
               'bat1': "{0:.2f}".format((bat1Mv) / 1000),
               'bat2': "{0:.2f}".format((bat2Mv) / 1000),
               'LastRunTime': str(LastRunTime),
               'iteration': str(iteration),
               'waitedForGpsFixIterations': str(waitedForGpsFixIterations)}

    httpsUriPath = '/mythweb/pibotmon/logging/imei/' + str(imei)

    httpsHostname = 'www.webarmadillo.net'
    httpBasicAuthUser = 'greg'
    httpBasicAuthPassword = 'ffff'

    uri = 'https://' + str(httpBasicAuthUser) + '@' \
          + str(httpsHostname) + str(httpsUriPath)

    try:

        r = requests.get(uri, params=payload, timeout=0.4, verify=False)
        print r.url
        logging.info(r.url)

    except Exception, e:

        logging.error('Could not send HTTPS logging: ' + str(e))


def dailyStatusOffSms(sms):

    # get the number
    number = str(sms[0]['Number'])
    reply = None

    # fish out the global
    global dailyStatus

    logging.info('Disabling regluar status checks')

    # disabled the Alarm by Nulling the values
    dailyStatus = ''

    # sort a message to send back
    reply = 'Daily status SMS being disabled!'

    # sent the SMS
    sendSms(number, reply)


def sendDebugMessage():

    # fetch global
    global sendStatus

    if debug is True:
        logging.debug('Debug is true, sending debug status')
        # pretend we have not sent a status
        # yes you might get a few ...
        sendStatus = True


def logUptime():

    logging.info('Uptime: ' + str(uptimeSec()) + ' secs')


def waitTillUptime(requiredUptime):

    _uptime = uptimeSecs()
    _loop = 0

    #
    # check we have been up one minute
    # otherwie mopi will not obey the shutdown call
    # plus it gives us time to get a goodish GPS fix
    #
    while _uptime < requiredUptime:

        # we have run at least once
        _loop += 1

        # wait a bit
        time.sleep(1)

        # get uptime
        _uptime = uptimeSecs()

        if debug is True:
            logging.debug('_uptime is: ' + str(_uptime)
                          + ', we have looped: ' + str(_loop) + ' times')

    logging.info('Uptime now: ' + str(_uptime) + ', uptime required: '
                 + str(requiredUptime) + ', we looped: '
                 + str(_loop) + ' secs')


def saveIterationAndLastRunTime():

    global iteration
    global LastRunTime

    # increase the iteration by one
    iteration += 1

    # and save the time
    LastRunTime = datetime.datetime.now()


def giveGpsChance():

    global waitedForGpsFixIterations

    waitedForGpsFixIterations = 0

    if gpsp.getCurrentNoFixes() > 0:

        logging.debug('Alreadt have a GPS fix')
        return

    # No GPS fix

    while gpsp.getCurrentNoFixes() < 1:
                # loop till we get 10 fixes... should not be long
                time.sleep(1)
                if debug is True:
                    logging.debug('No gps fixs!!! We have looped: '
                                  + str(waitedForGpsFixIterations))
                waitedForGpsFixIterations += 1

                if _loop == 60:

                    logging.debug('Reach 60 tries, breaking')
                    break

    if gpsp.getCurrentNoFixes > 1:

        # GPS Fix ...
        logging.info('Got a GPS fix.  We looped: ' 
                     + str(waitedForGpsFixIterations) + ' times, uptime now: '
                     + str(uptimeSecs()))

    else:
        logging.error('No GPS FIX!!!,tried: '
                      + str(waitedForGpsFixIterations) + ' times')


def uptimeSecs()

    uptime, idletime = [float(f) for f in open("/proc/uptime")
                        .read().split()]

    return uptime


if __name__ == '__main__':

    # check we are running as sudo
    if os.geteuid() != 0:
        exit("You need to have root privileges to run this script.\n"
             + "Please try again, this time using 'sudo'. Exiting.")

    # setup logger
    try:
        logging.basicConfig(filename=logfile, level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s'
                                   + ' %(funcName)s %(message)s')
    except Exception, e:
        print 'Logging problem' + str(e)
        sys.exit(1)

    # log we have started
    logging.info('Started ...')

    # record the uptime
    logUptime()

    # load config
    loadConfig()

    # set iteration and LastRunTime
    saveIterationAndLastRunTime()

    # create a gpsPollerthread and asks it to start
    gpsp = GpsPoller()
    gpsp.start()

    # create a mopi object to query
    mopi = mopiapi()

    # setup the modem - takes a few secs ...
    # so the GPS thread can be on its way :w
    setUpGammu()

    # if we have a modem configured
    # check SMS, check the anchor watch and check the daily status
    if sm:
        if debug is True:
            logging.debug('Going to try getting SMS messages getSms()')
        getSms()

    # check and spin till we have been up 60 secs
    # otherwise mopi will not shutdown
    waitTillUptime(50)

    # for debug...
    sendDebugMessage()

    # check anchor alarm
    checkAnchorAlarm()

    # set the bilge Switch state
    setBilgeSwitchState()

    # check we need to send regular status
    checkRegularStatus()

    # check to see we need to send a daily status message
    checkDailyStatus()

    # check to see if we still need to send a status message
    # (daily alarm may have not fired or been set)
    sendAndLogStatus()

    # check bilge is ok
    checkBilge()

    # log status in case nothing has fired log status anyway
    checkLogStatus()

    # setPowerOnDelay
    setPowerOnDelay()

    # save the config at the end, once ...
    saveConfig()

    # Check we got a GPS fix, otherwise wait another 60 secs
    # to give GPS a chance to fix and save almernac
    giveGpsChance()

    # send server logging Status
    sendHttpsLogging()

    # Wait till we get to 60 secs uptime
    waitTillUptime(60)

    # we think we are done ..
    # stop the thread and wait for it to join
    logging.info('Killing gps Thread...')
    gpsp.running = False
    gpsp.join()  # wait for the thread to finish what it's doing

    # log we are stopping ...
    logging.info('Done. Exiting.')

    exit(0)

# done
# vim:ts=4:sw=4:expandtab
# syntax on
# filetype indent plugin on
# set modeline
