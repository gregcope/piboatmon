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
import datetime

# global Vars
phone = ''
boatname = ''
debug = False
wakeInNSecs = ''
alarmRange = ''
regularStatus = ''

# some object handles
gpsd = None
sm = None
configP = None
gpsp = None

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
                            logging.debug('GPS thread stats: LAT ' + str(self.avLat) + ' LON ' +str(self.avLon) + ' VEL ' + str(self.avSpeed) + ' HEAD ' + str(self.avHeading) + 'T LAT +/- ' + str(self.avEpx) + ' LON +/- ' + str(self.avEpy) + ' No. fixes ' + str(self.numFixes))

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
        # defult to ''
        alarmRange = ''
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
        logging.debug('About to put gammu into debug mode logging to: ' + str(logfile))
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

def sendSms(number, txt):

    # send the message to the phone
    # trap any nonesense

    # Prefix with boatname
    txt = boatname + ': ' + txt

    global phone
    if number is '':
        # no number so use global phone
        number = phone

    if number is '':
        logging.error('Trying to send a SMS to a phone that is not set - phone: ' + str(number))
        # give up
        return

    if debug is True:
        logging.debug('Trying to send SMS message: ' + str(txt) + ' to: ' + str(number))

    # go for it
    message = { 'Text': txt, 'SMSC': {'Location': 1}, 'Number': number }

    try:

        if debug is True:
            logging.debug('About to try sm.SendSMS(message)')

        sm.SendSMS(message)
        logging.info('Message sent to: ' + str(number))

    except Exception, e:
        logging.error('Exception: ', e)

    # done
    return

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
        logging.error('Failed sm.GetSMSStatus() ', e)

    _remain = _status['SIMUsed'] + _status['PhoneUsed']
    + _status['TemplatesUsed']

    logging.info('There are: ' + str(_remain) + ' SMS(s) to deal with')

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
        sendStatusSms(sm)
        _understoodSms = True

    # no idea what the SMS is...
    if _understoodSms is False:
        logging.info('Could not parse SMS message: ' + str(_txt))

    # finished

def setRegularStatusSms(sms):

    # get the number
    number = str(sms[0]['Number'])
    _txt = sms[0]['Text'].lower()
    _lowertxt = txt.lower()
    reply = None

    # fish out the global var
    global regularStatus

    results = re.search("set regular status (\d+)UTC", _lowertxt)

    # if we have a match
    if results:

        regularStatus = results.group(1)
        logging.info('Setting regular status update at : ' + str(regularStatus) + ' UTC')

        # save the config for next checks
        saveConfig()

        # reply
        reply = 'Regular status setup to be sent around: ' + str(regularStatus) + 'UTC each day (depends on wakeUp)'

    # could not parse results
    else:
        logging.error('Could not parse new regular status update: ' + str(txt))
        reply = 'Could not parse new regular status update: ' + str(txt)

    # sent the SMS
    sendSms(number, reply)

def getStatus():

    return 'Everything peachy'

def sendStatusSms(sms):

    # get the number
    number = str(sms[0]['Number'])
    reply = getStatus()

    sendSms(number, reply)

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
            logging.info('Setting new anchor alarm: ' + alarmRange)

        else:

            # less than 10
            reply = 'New Anchor Alarm appears to be less than 10M ... please try again (with a higher number)'
            loggin.info('New Anchor Alarm appears to be less than 10M.  SMS reply asking for higher number')
            sendSms(number, reply)
            return

    _presentLat, _presentLon = gpsp.getCurretAvgLatLon()
    reply = 'Anchor Alarm being set for Lat: ' + str(_presentLat) + ' Lon: ' + str(_presentLon) + ' Alarm range: ' + str(alarmRange)

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

    if 'true' in _lowertxt:
        debug = True
        logging.info('Setting debug to True')
        reply = 'Setting debug to True'

    elif 'off' in _lowertxt:
        debug = False
        logging.info('Setting debug to False')
        reply = 'Setting debug to False'

    else:
        logging.info('No idea what that txt was...')
        reply = 'Could not parse debug message : ' + _lowertxt

    sendSms(number, reply)

def sendInstructionsSms(sms):

    # get the number
    number = str(sms[0]['Number'])

    # Put are reply together
    reply = 'Commands:\nupdate phone NUM\nregular status TIME UTC\nregular status off\nset anchor alarm DIS_IN_M\nanchor alarm off\ndebug\nsend state\nsend instructions'

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

def logStatus():

    # log status
    logging.info(getStatus())

def checkRegularStatus():

    # check that have not sent a status message in timeframe

    # what is the time now?
    _now = datetime.datetime.now().time()

    # some defaults
    _min = 0
    _hour = 0
    _nestAlarm = None

    # split regularStatus into hours / minutes
    p = re.compile('..')
    _hour, _minute = p.findall(str(regularStatus))

    # http://www.saltycrane.com/blog/2008/06/how-to-get-current-date-and-time-in/
    if _hour >=0 and _minute >= 0:
        _nextAlarm = datetime.datetime(_now.year, _now.month, _now.day, 
                int(hour), int(minute), 0)
    else:
        logging.error('Cannot split regularStatus into _hour / _min: ' + str(regularStatus))
        # as we have nothing to compare, bale...
        return

    if debug is True:
        logging.debug('Next regular Status check is due: ' + _now)

    if _now > _nextAlarm:

        # alarm fired, so therefore get status
        message = getStatus()

        logging.info('Regular Status check: ' + str(message))

        # try and send the SMS
        if phone and sm:
            # sent the SMS
            sendSms(phone, message)
        else:
            logging.error('No Phone or SM to send Regular Status check')
    # done

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

if __name__ == '__main__':

    # setup logger
    try:
        logging.basicConfig(filename=logfile, level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(funcName)s %(message)s')
    except Exception, e:
        print 'Logging problem', e
        sys.exit(1)
    
    logging.info('Started ...')

    # load config
    loadConfig()

    # create a gpsPollerthread and asks it to start
    gpsp = GpsPoller()
    gpsp.start()

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

    # log status
    logStatus()

    # check to see we need to send a status message
    checkRegularStatus()

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
