#! /usr/bin/python

# GPS thread Parts based on / Written by;
# Dan Mandle http://dan.mandle.me September 2012
# License: GPL 2.0
# and
# http://stackoverflow.com/questions/6146131/python-gps-module-reading-latest-gps-data

# mopi API stolen from:
# https://github.com/hamishcunningham/pi-tronics/blob/master/simbamon/mopiapi.py

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

# global Vars
phone = ''
boatname = ''
debug = False
wakeInNSecs = ''
alarmRange = ''
regularStatus = ''
lastRegularStatusCheck = ''
batteryOkMVolts = ''
sendStatus = False
logStatus = True

# some object handles
gpsd = None
sm = None
configP = None
gpsp = None
mopi = None

# mopi API config
# For at least mopi firmware vX.YY...
FIRMMAJ=3
FIRMMINR=5

# Number of times to retry a failed I2C read/write to the MoPi
MAXTRIES=3

# some hard config
logfile = '/home/pi/rpi/files/boatmon.log'
configFile = "/home/pi/rpi/files/boatmon.config"

###### Code below here

class mopiapi():
        device = 0xb
        maj = 0
        minr = 0

        def __init__(self, i2cbus = -1):
                if i2cbus == -1:
                        i2cbus = self.guessI2C()
                self.bus = smbus.SMBus(i2cbus)
                [self.maj, self.minr] = self.getFirmwareVersion()
                if self.maj != FIRMMAJ or self.minr < FIRMMINR:
                        raise OSError(errno.EUNATCH, "Expected at least MoPi firmware version %i.%02i, got %i.%02i instead." % (FIRMMAJ, FIRMMINR, self.maj, self.minr))

        def getVoltage(self, input=0):
                if input == 1:
                        return self.readWord(0b00000101) # 5
                elif input == 2:
                        return self.readWord(0b00000110) # 6
                else:
                        return self.readWord(0b00000001)

        def setPowerOnDelay(self, poweron):
                self.writeWord(0b00000011, poweron)

        def setShutdownDelay(self, shutdown):
                self.writeWord(0b00000100, shutdown)

        def getPowerOnDelay(self):
                return self.readWord(0b00000011)

	def getFirmwareVersion(self):
		word = self.readWord(0b00001001) # 9
		return [word >> 8, word & 0xff]

        def baseReadWord(self, register):
                tries = 0
                data = 0xFFFF
                error = 0
                while data == 0xFFFF and tries < MAXTRIES:
                        error = 0
                        try:
                                data = self.bus.read_word_data(self.device, register)
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
                        time.sleep(0.02) # slight delay to allow write to take effect
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
            # Rev2 of RPi switched the i2c address, so return the right one for the board we have 
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

        logging.info('Started gpsp thread')

        # while the thread is running
        while gpsp.running:

            # try and get a gpsd report
            try:
                report = gpsd.next()

                #if debug is True:
                   # logging.debug('Got a gpsd report' + str(report))

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

                 #       if debug is True:
                         #   logging.debug('GPS thread stats: LAT ' + str(self.avLat) + ' LON ' +str(self.avLon) + ' VEL ' + str(self.avSpeed) + ' HEAD ' + str(self.avHeading) + 'T LAT +/- ' + str(self.avEpx) + ' LON +/- ' + str(self.avEpy) + ' No. fixes ' + str(self.numFixes))

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

        if self.numFixes == 0:
            # No GPS fix (yet)
            return 'NO GPS FIX!'

        # if the number of fixes is low, or EP low
        if self.numFixes < 10 or int(self.avEpx) > 15 or int(self.avEpy) > 15:

            # prefix poor fix
            prefix = prefix + 'POOR '

        # rounding
        roundedAvEpx = int(self.avEpx)
        roundedAvEpy = int(self.avEpy)
        roundedAvHeading = int(self.avHeading)

        # find the biggest EP error and report on that
        roundedEp = max(roundedAvEpx, roundedAvEpy)

        # convert km/h to knots
        roundedAvSpeedKn = int(self.avSpeed / 0.539957)

        # return what we have
        return 'GPS fix: ' + prefix + 'Lat ' + str(self.avLat) + ' Lon ' + str(self.avLon) + ' ' + str(roundedAvSpeedKn) + 'KN HEAD ' +str(roundedAvHeading) + 'T EP +/-' + str(roundedEp)

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
    configP.set('main', 'lastRegularStatusCheck', str(lastRegularStatusCheck))
    configP.set('main', 'batteryOkMVolts', str(batteryOkMVolts))
    configP.set('main', 'sendStatus', str(sendStatus))

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
    global lastRegularStatusCheck
    global batteryOkMVolts
    global sendStatus

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
        # defult to ''
        lat = ''
    try:
        lon = configP.get('main', 'lon')
    except:
        # defult to ''
        lon = ''
    try:
        alarmRange = configP.getint('main', 'alarmRange')
    except:
        # defult to ''
        alarmRange = ''
    try:
        regularStatus = configP.get('main', 'regularStatus')
    except:
        # defult to ''
        regularStatus = ''
    try:
        lastRegularStatusCheck = configP.get('main','lastRegularStatusCheck')
    except:
        lastRegularStatusCheck = ''

    try:
        batteryOkMVolts = configP.get('main','batteryOkVolts')
    except:
        batteryOkMVolts = 1100

    try:
        sendStatus = configP.getboolean('main', 'sendStatus')
    except:
        sendStatus = False

    logging.info(str(configP.items('main')))

def setUpGammu():

    # fish out the global var
    global sm

    # setups the SMS gammu system
    # returns true if all good
    # return false if there are issues

    if debug is True:
        logging.debug('About to put gammu into debug mode logging to: ' + str(logfile))
        gammu.SetDebugLevel('errorsdate')
        gammu.SetDebugFile(logfile)

    # create a state machine
    sm = gammu.StateMachine()

    # try and read the config
    try:
        sm.ReadConfig(Filename = '/home/pi/.gammurc')

    except Exception, e:
        logging.error('gammu Readconfig failed' + str(e))

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
            logging.error('setUpGammu - sm.Init failed' +str(e))
            sm = None

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
    global gpsp

    if debug is True:
        logging.debug('alarmRange is: ' + str(alarmRange) + ' Lat: ' +str(lat) + ' Lon: ' + str(lon))

    if alarmRange > 1:

        # check we have a lat/lon to compare to
        if lat != '' and lon !='':

            # if we have a lat/lon to compare to
            # get fix
            while gpsp.getCurrentNoFixes() < 10:
                # loop till we get 10 fixes... should not be long
                time.sleep(1)
                if debug is True:
                    logging.debug('Not enough gps fixes - we want 10 - gpsp.getCurrentNoFixes()' + str(gpsp.getCurrentNoFixes()))

            # fetch a good fix
            newlat, newlon = gpsp.getCurretAvgLatLon()
            if debug is True:
                logging.debug('Present lat: ' + str(newlat) + ' lon: ' + str(newlon))

            # compare fix with saved config
            movedDistanceKm = distance(float(lat), float(lon), float(newlat), float(newlon))
            # change the distance to meters rounded (not 100% accurate)
            movedDistanceM = int(movedDistanceKm * 1000)

            if debug is True:
                logging.debug('Distance moved is: ' + str(movedDistanceM))

            # work out if less than alarmRange
            if movedDistanceM > alarmRange:

                if debug is True:
                    logging.info('Moved distance: ' + str(movedDistanceM) + 'M is more than alarmRange: ' + str(alarmRange) + 'M')

                txt = 'ANCHOR ALARM FIRED.  Distance moved: ' + str(movedDistanceM) +'M, Alarm distrance set: ' + str(alarmRange) + 'M. Present position/heading LAT: ' + str(newlat) + ', LON: ' + str(newlon)

                if sm and phone:
                    sendSms(txt)
                else:
                    logging.error('No SMS statemachine, or phone configured - cannot send anchor alarm SMS')

        else:
            # lat / lon are empty !!!!
            logging.error('Anchor alarm set: ' + str(alarmRange) + ' Lat/Lon are empty')
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
        logging.error('Trying to send a SMS to a phone that is not set - phone: ' + str(_number))
        # give up
        return False

    if _txt is '':
        logging.error('trying to send an empty SMS?')
        return False

    # Prefix with boatname and time
    _txt = datetime.datetime.now().strftime("%a %X") + ' ' + boatname + ': ' + _txt

    if debug is True:
        logging.debug('Trying to send SMS message: ' + str(_txt) + ' to: ' + str(_number))

    # go for it
    message = { 'Text': _txt, 'SMSC': {'Location': 1}, 'Number': _number }

    try:

        if debug is True:
            logging.debug('About to try sm.SendSMS(message)')

        sm.SendSMS(message)
        logging.info('Message sent to: ' + str(_number))

        # yay it worked!!!!
        return True

    except Exception, e:

        # Ops... 
        logging.error('Exception: ' +str(e))
        return False

def distance(lat1, lon1, lat2, lon2):

    # stolen from https://github.com/sivel/speedtest-cli/blob/master/speedtest_cli.py
    """Determine distance between 2 sets of [lat,lon] in km"""

    # assume a round earth ...
    radius = 6371  # km

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
        logging.error('Failed sm.GetSMSStatus() ' +str(e))

    _remain = _status['SIMUsed'] + _status['PhoneUsed']
    + _status['TemplatesUsed']

    logging.info(str(_remain) + ' SMS(s) to deal with')

    if _remain == 0:
        return

    while _remain > 0:

        if _start:

            cursms = sm.GetNextSMS(Start = True, Folder = 0)
            if debug is True:
                logging.debug('In start processing SMS: ' + str(cursms))

            # we got some to deal with
            _start = False
            processSMS(cursms)
            gotSMS += 1
        
        else:

            if debug is True:
                logging.debug('In else processing SMS: ' + str(cursms))

            cursms = sm.GetNextSMS(Start = True, Folder = 0)
            processSMS(cursms)
            gotSMS += 1

        # delete the SMS
        for x in range(len(cursms)):
            logging.info('Deleting SMS no: ' + str(x))
            if debug is True:
                logging.debug('About to delete SMS in location: ' + str(cursms[x]['Location']))
            sm.DeleteSMS(cursms[x]['Folder'], cursms[x]['Location'])

        _remain = _remain - len(cursms)
        sms.append(cursms)

def processSMS(sms):

    # lower text the message so we can parse it
    # anoying the iPhone capitalising first char
    _txt = sms[0]['Text']
    _lowertxt = _txt.lower()
    _understoodSms = False

    # as we might set it grab it
    global debug
    global sendStatus

    if 'debug' in _lowertxt:
        debugSms(sms)
        _understoodSms = True

    # might be a phone set command
    if 'update phone' in _lowertxt:
        updatePhoneSms(sms)
        _understoodSms = True
    
    # might be an anchor alarm off
    if 'anchor alarm off' in _lowertxt:
        anchorAlarmOffSms(sms)
        _understoodSms = True

    # might be a config message
    if 'config' in _lowertxt:
        configSms(sms)
        _understoodSms = True

    # set the anchor alarm
    if 'set anchor alarm' in _lowertxt:
        setAnchorAlarmSms(sms)
        _understoodSms = True

    # might be a set regular status
    if 'set regular status' in _lowertxt:
        setRegularStatusSms(sms)
        _understoodSms = True

    # might be a config txt to set the battery mV
    if 'set battery ok volts' in _lowertxt:
        setBatteryOkMVoltsSms(sms)
        _understoodSms = True

    if 'set sleep time' in _lowertxt:
        setWakeInNSecsSms(sms)
        _understoodSms = True

    # or we might be switching regular status off
    if 'regular status off' in _lowertxt:
        regularStatusOffSms(sms)
        _understoodSms = True

    # send instructions SMS
    if 'send instructions' in _lowertxt:
        sendInstructionsSms(sms)
        _understoodSms = True

    # send a status txt
    if 'send status' in _lowertxt:
        # fire at least a statusTxt or regularStatus to avoid 2 SMS
        sendStatus == True
        _understoodSms = True

    if 'set boatname' in _lowertxt:
        setBoatnameSms(sms)
        _understoodSms = True

    # no idea what the SMS is...
    if _understoodSms is False:
        logging.info('Could not parse SMS message: ' + str(_txt))

    # finished

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

    results = re.search("set battery ok volts (\d{4})", _lowertxt)

    # if we have a match
    if results:

        batteryOkMVolts = results.group(1)

        # save the config for next checks
        saveConfig()
        # reply
        reply = 'Battery OK volts set to: ' + str(batteryOkMVolts) + ' mV'
        logging.info(reply)

    # could not parse results
    else:
        reply = 'Could not set battery ok volts: ' + str(_txt) + '. Must be in 4 digits long e.g. 1300'
        logging.error(reply)

    # sent the SMS
    sendSms(number, reply)

def setRegularStatusSms(sms):

    # get the number
    number = str(sms[0]['Number'])
    _txt = sms[0]['Text']
    _lowertxt = _txt.lower()
    reply = None

    # fish out the global var
    global regularStatus

    results = re.search("set regular status (\d{4})", _lowertxt)

    # if we have a match
    if results:

        regularStatus = results.group(1)

        # save the config for next checks
        saveConfig()

        # reply
        reply = 'Regular status setup to be sent around: ' + str(regularStatus) + ' UTC each day (depends on wakeUp)'
        logging.info(reply)

    # could not parse results
    else:
        reply = 'Could not parse new regular status update: ' + str(_txt) + 'Needs to be 4 digit 24hr clock notation'
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

                # save the config for next checks
                saveConfig()

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

    # set the PowerOnDelay to wak
    if wakeInNSecs < 60:
        logging.error(str(wakeInNSecs) + ' below 60 secs, setting to 60 min...')
        wakeInNSecs = 60

    logging.info('Setting mopi mopi.setPowerOnDelay to: ' + str(wakeInNSecs))

    mopi.setPowerOnDelay(wakeInNSecs)

    print 'Setting wake on delay to: ' + str(wakeInNSecs)

def getInputmV():

    _input1mv = mopi.getVoltage(1)
    _input2mv = mopi.getVoltage(2)
    
    return _input1mv, _input2mv

def getBatteryText():

    status = ''

    # get battery volts from mopi
    _input1mv, _input2mv = getInputmV()

    # for each battery define a state
    # above 1300 charging
    # above 1100 ok
    # lower than 1100 low
    # 0 == missing/dead
    # below 
    if _input1mv < 1300:
       status = status + 'Batt1 Charging: ' + str(_input1mv / 1000) + 'V'
    elif _input1mv > batteryOkMVolts:
       status = status + 'Batt1 Ok: ' + str(_input1mv / 1000) + 'V'
    elif _input1mv == batteryOkMVolts:
       status = status + 'Batt1 Missing: 0V'
    elif _input1mv < 1100:
       status = status + 'Batt1 Low: ' + str(_input1mv / 1000) + 'V'
    else:
       status = status + 'Batt1 state unkown'

    # Battery2 is assumed to be a 9v
    # above 9000 is Ok
    # below 5200 is low
    # 0 == mising/dead
    if _input2mv > 9000:
       status = status + ' Batt2 Ok: ' + str(_input1mv / 1000) + 'V'
    elif _input2mv == 0:
       status = status + ' Batt2 Missing: 0V'
    elif _input2mv < 5200:
       status = status + ' Batt2 Low: ' + str(_input1mv / 1000) + 'V'
    else:
       status = status + 'Batt2 state unkown'

    return status

def checkBattery():

    # get battery volts from mopi
    _input1mv, _input2mv = getInputmV()

    if _input1mv > batteryOkMVolts:
        return True
    else:
        return False

def checkBilge():

    return True

def checkBilgeText():

    if checkBilge() is True:
        status = 'Bilge Ok'
    else:
        status = 'BILGE ALARM'

    logging.info(status)

    return status

def getStatusText():

    # build a status string
    status = 'Status: ' + getBatteryText() + ' ' + checkBilgeText() + ' ' + gpsp.getCurrentAvgDataText()

    if checkBilge() and checkBattery():
        status = 'OK ' + status
    else:
        status = 'NOT OK ' + status

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

    # lookfing for string like
    # set anchor alarm 100m or
    # set anchor alarm

    # parse the SMS for alarm range
    results = re.search("set anchor alarm (\d+)m", _lowertxt)
    if results:

        _newRange = results.group(1)
        if debug is True:
            logging.debug('Found the following regex results: ' + str(_newRange))

        if _newRange > 10:

            # so should have something sensible to set the alarmRange to
            # make it an int for sanity...
            alarmRange = int(_newRange)

        else:

            # less than 10
            reply = 'New Anchor Alarm appears to be less than 10M ... please try again (with a higher number)'
            loggin.info(reply)
            sendSms(number, reply)
            saveConfig()
            return

    else:
        # not re match set 20M as default
        alarmRange = 20
        
    # so we should have something sensible by now ..
    _presentLat, _presentLon = gpsp.getCurretAvgLatLon()
    reply = 'Anchor Alarm being set for Lat: ' + str(_presentLat) + ' Lon: ' + str(_presentLon) + ' Alarm range: ' + str(alarmRange)

    logging.info(reply)
    saveConfig()
    
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
    _newPhoneRegEx = re.search("update phone (\+?\d+)", _lowertxt)
    _newPhone = _newPhoneRegEx.group(1)

    if _newPhone is not '':

        if debug is True:
            logging.debug('Found new phone number: ' + str(_newPhone))

        # keep the old phone
        oldphone = phone
        phone = _newPhone

        # got this far, should have something sensible to set
        logging.info('Changing phone from: ' + str(oldphone) + ' to: ' + str(_newPhone))
        # save the config for next checks
        saveConfig()

        if oldphone != '':
            # sort a message to reply back letting original phone know of reset
            reply = ': New phone being set: ' + str(phone) + '.  To reset the phone back to this phone, reply to this SMS with:\n\nupdate phone ' + str(oldphone)

            # sent the reply SMS
            sendSms(oldphone, reply)

        # reply to _newphone
        reply = 'New phone being set to: ' + str(phone)
        sendSms(phone, reply)

    else:
        logging.error('Not a phone number we could parse in: ' + str (sms[0]['Text']))

def debugSms(sms):

    # either put debug on/off
    _lowertxt = sms[0]['Text'].lower()
    number = str(sms[0]['Number'])

    reply = None

    # set global var
    global debug

    if 'true' or 'on' in _lowertxt:
        debug = True
        reply = 'Setting debug to True'
        logging.info(reply)

    elif 'off' in _lowertxt:
        debug = False
        reply = 'Setting debug to False'
        logging.info(reply)

    else:
        logging.info('No idea what that txt was...')
        reply = 'Could not parse debug message : ' + _lowertxt

    sendSms(number, reply)

def sendInstructionsSms(sms):

    # get the number
    number = str(sms[0]['Number'])

    # Put are reply together
    reply = 'Commands:\nupdate phone NUM\nregular status TIME UTC\nregular status off\nset anchor alarm DIS_IN_M\nanchor alarm off\ndebug\nsend state\nset sleep time MINS\nset battery ok volts Mvolts\nsend instructions'

    # sent the SMS
    sendSms(number, reply)

def anchorAlarmOffSms(sms):

    # get the number
    number = str(sms[0]['Number'])
    reply = None

    logging.info('Disabling the Anchor Alarm')

    # fish out the global vars!
    global lat
    global lon
    global alarmRange

    # disabled the Alarm by Nulling the values
    lat = ''
    lon = ''
    alarmRange = ''

    # save the config for next checks
    saveConfig()

    # sort a message to send back
    reply = ': Anchor alarm being diabled!'
   
    # sent the SMS
    sendSms(number, reply)

def checkLogStatus():

    if logStatus is True:
        # log status
        logging.info(getStatusText())
    elif debug is True:
        logging.debug('called, but already run as logStatus is: ' + str(logStatus))

def checkRegularStatus():

    # if regularStatus is not set bale
    if regularStatus == '':
        logging.info('No regularStatus check set')
        return

    # we might set this if we run
    global lastRegularStatusCheck
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
        _lastRun = datetime.datetime.strptime(lastRegularStatusCheck, "%Y-%m-%d %H:%M:%S.%f")

        if _lastRun.date() == _now.date():

            # we ran today ... exit
            logging.info('Ran today already: ' + str(_lastRun))

            return

    except ValueError:
        _lastRun = None
        logging.info('lastRegularStatusCheck: ' + str(lastRegularStatusCheck) + 'Could not be parsed into a date')

    # so ... if we got this far we need to check the time

    # split regularStatus into hours / minutes
    p = re.compile('..')

    try:
        _hour, _minute = p.findall(str(regularStatus))
    except ValueError:
        logging.error('Could not parse regularStatus: ' + str(regularStatus) + ' into _hour, _minute')

    # http://www.saltycrane.com/blog/2008/06/how-to-get-current-date-and-time-in/
    if _hour >=0 and _minute >= 0:
        _nextAlarm = datetime.datetime(_now.year, _now.month, _now.day, 
                int(_hour), int(_minute), 0)
        logging.info('Next regular check due: ' + str(_nextAlarm))

    else:
        logging.error('Cannot split regularStatus into _hour / _min: ' + str(regularStatus))
        # as we have nothing to compare, assume we need to run

    if _now > _nextAlarm:

        if debug is True:
            logging.debug('alarm fired')

        # alarm fired, so therefore send status
        sendStatus = True

        if sendAndLogStatus() is True:

            # clear any sendStatus flag
            # save config to preserve fact we ran in lastRegularStatusCheck
            sendStatus = False
            lastRegularStatusCheck = _now
            saveConfig()

            logging.info('Regular SMS sent, lastRegularStatusCheck updated to: ' + str(lastRegularStatusCheck))

        else:
            # log the fact we ops'ed
            logging.error('Failed to send regular SMS - should try again next run')

def sendAndLogStatus():

    # sends a status message - either add hoc or regular
    # check to see if we need to send a status message (ie failed, or each time we run)

    # fish out the global
    global sendStatus
    global logStatus

    _sent = False

    if debug is True:
        logging.debug('sendStatus is: ' +str(sendStatus) + ', logStatus is: ' +str(logStatus))

    if sendStatus is True:

        # get some text
        message = getStatusText()
        logging.info(str(message))

        # clear the flag
        logStatus = False

        if sendSms(phone, message):
            # went ok - clear any flags
            sendStatus = False
            _sent = True
        else:
            logging.error('Failed to send status ... will try next run as sendStatus is: ' + str(sendStatus))
            sendStatus = True

        # either way save state
        saveConfig()

    return _sent

def checkBilgeSwitch():


    if debug is True:
        logging.debug('Setting up RPi.GPIO pins')

    # from http://razzpisampler.oreilly.com/ch07.html
    RPi.GPIO.setmode(RPi.GPIO.BCM)
    RPi.GPIO.setup(18, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)

    _input18State = RPi.GPIO.input(18)

    if _input18State is False:

        # BilgeSwitch is on ... Ops:

        messagge = 'Bilge Switch is ON !!!'
        logging.info(message)

        # try and send the SMS
        sendSms(phone, message)

    else:
        logging.info('Bilge Swich is off')

def regularStatusOffSms(sms):

    # get the number
    number = str(sms[0]['Number'])
    reply = None

    logging.info('Disabling regluar status checks')

    # disabled the Alarm by Nulling the values
    regularStatus = ''

    # save the config for next checks
    saveConfig()

    # sort a message to send back
    reply = 'Regular status SMS being disabled!'

    # sent the SMS
    sendSms(number, reply)

def sendDebugMessage():

    if debug is True:
        logging.debug('Debug is true, sending debug status')
        sendStatus = True
        sendAndLogStatus()

if __name__ == '__main__':

    # check we are running as sudo
    if os.geteuid() != 0:
        exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")

    # setup logger
    try:
        logging.basicConfig(filename=logfile, level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(funcName)s %(message)s')
    except Exception, e:
        print 'Logging problem' + str(e)
        sys.exit(1)
    
    logging.info('Started ...')

    # load config
    loadConfig()

    # create a gpsPollerthread and asks it to start
    gpsp = GpsPoller()
    gpsp.start()

    # create a mopi object to query
    mopi = mopiapi()

    # setup the modem - takes a few secs ...
    # so the GPS thread can be on its way :w
    setUpGammu()

    # if we have a modem configured
    # check SMS, check the anchor watch and check the regular status
    if sm:
        if debug is True:
            logging.debug('Going to try getting SMS messages getSms()')
        getSms()

    # check anchor alarm
    checkAnchorAlarm()

    # check to see we need to send a regular status message
    checkRegularStatus()

    # check to see if we still need to send a status message (regular alarm may have not fired or been set)
    sendAndLogStatus()

    # check bilge is ok
    checkBilgeSwitch()

    # log status in case nothing has fired log status anyway
    checkLogStatus()

    # for debug...
    sendDebugMessage()

    # setPowerOnDelay
    setPowerOnDelay()

    # we think we are done ..
    # stop the thread and wait for it to join
    logging.info('Killing gps Thread...')
    gpsp.running = False
    gpsp.join() # wait for the thread to finish what it's doing
    logging.info('Done. Exiting.')

    exit(0)

# done
# vim:ts=4:sw=4:expandtab
# syntax on
# filetype indent plugin on
# set modeline
