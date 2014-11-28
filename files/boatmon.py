#!/usr/bin/python

"""
Python script to check stuff then send and SMS
"""

import gps
import time
import gammu
import re
import ConfigParser
import math
import sys

# some defaults
configFile = "/home/pi/rpi/files/boatmon.config"

lat = ''
lon = ''
# has to be more than numberGpsFixesToAverage
gpsFixTimeout = ''
phone = ''
boatname = ''
debug = False
# gammu statemachine
sm = None
wakeInNSecs = ''
numberGpsFixesToAverage = ''
alarmRange = ''
regularStatus = ''

def gpsfix():

    """
    connect to the gps daemon
    loop whilst we wait for a fix
    return lat, log, speed, and heading 
    """

    # Listen on port 2947 (gpsd) of localhost
    try:
        session = gps.gps("localhost", "2947")
    except:
        print 'Ops... gpsd not running right?' 
        print 'Hint: sudo /etc/init.d/gpsd start'
        exit(1)
    session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

    # loop whilst we wait for a fix
    _loop = 0
    _lat = 0
    _lon = 0
    _speed = 0
    _heading = 0
    _epx = 0
    _epy = 0 
    _sumLat = 0
    _sumLon = 0
    _sumSpeed = 0
    _sumHeading = 0
    _sumEpx = 0
    _sumEpy = 0

    while True:
        try:
            report = session.next()
            if report['class'] == 'TPV':

                _loop += 1
                #print 'GPS fix Loop is: ', _loop
                print 'GPS report is ' + str(report)
                if ( hasattr(report, 'speed') and hasattr(report, 'lon') 
                        and hasattr(report, 'lat') and hasattr(report, 'track')
                        and hasattr(report, 'epx') and hasattr(report, 'epy') ):
                    print
                    print 'FIX!'
                    print 
                    # we got a fix... break
                    _sumLat = _sumLat + report.lat
                    _sumLon = _sumLon + report.lon
                    _sumSpeed = _sumSpeed + report.speed
                    _sumHeading = _sumHeading + report.track
                    _sumEpx = _sumEpx + report.epx
                    _sumEpy = _sumEpy + report.epy

                    # if we have enough data, calc average and break
                    if _loop == numberGpsFixesToAverage:
                        _lat = _sumLat / numberGpsFixesToAverage
                        _lon = _sumLon / numberGpsFixesToAverage
                        _speed = _sumSpeed / numberGpsFixesToAverage
                        _heading = _sumHeading / numberGpsFixesToAverage
                        _epx = _sumEpx / numberGpsFixesToAverage
                        _epy = _sumEpy / numberGpsFixesToAverage
                        break

                if _loop > gpsFixTimeout:
                    # Ops, we failed to get a fix in time
                    break

                # no fix, sleep 1 sec
                time.sleep(1)

        except StopIteration:
            session = None
            print "GPSD has terminated"

    # Ops, we bailed
    if _loop > gpsFixTimeout:
       return (0, _lat, _lon, _speed, _heading)

    # all good
    return (1, _lat, _lon, _speed, _heading)

def sendSMS(phoneNum, txt, sm):

    # for a give phoneNum and txt message
    # send the message to the phone
    # trap any nonesense
    print 'Sending txt:' + str(txt) + ', to: ' + str(phoneNum)

    # go for it
    message = { 'Text': txt, 'SMSC': {'Location': 1}, 'Number': phoneNum }

    print 'About to send message'
    try:
        # to make this barf, wrap the phone num in single quotes
        sm.SendSMS(message)
        print 'Message sent'
        sent = True
        print 'Sent is: ' + str(sent)
    except Exception as inst:
        print 'Pants failed to send message...'
        print type (inst)
        print inst
        sent = False

    # done
    print 'returning sent = ', str(sent)
    return sent

def getSMS(sm):

    # lifted from
    # http://osdir.com/ml/linux.drivers.gammu/2005-07/msg00018.html
    # set this to nothing
    sms = []
    _status = None
    _remain = 0
    _start = True
    _remain = 0
    cursms = None

    # get SMS message for this number
    gotSMS = 0

    try:
        print 'GetSMSStatus() ...'
        _status = sm.GetSMSStatus()
        print 'Done'
    except Exception as inst:
        print 'Pants failed to get SMSStatus ...'
        print type (inst)
        print inst

    _remain = _status['SIMUsed'] + _status['PhoneUsed'] 
    + _status['TemplatesUsed']
    print 'there are: ', _remain, 'sms to deal with'

    if _remain == 0:
        return False

    while _remain > 0:
        if _start:
            print 'in start if Processing sms: ' + str(cursms)
            cursms = sm.GetNextSMS(Start = True, Folder = 0)
            _start = False
            processSMS(cursms, sm)
            gotSMS += 1
        else:
            print 'in else: ' + str(cursms)
            cursms = sm.GetNextSMS(Location = cursms[0]['Location'], Folder = 0)
            processSMS(cursms, sm)
            gotSMS = 1
        for x in range(len(cursms)):
            sm.DeleteSMS(cursms[x]['Folder'], cursms[x]['Location'])
        _remain = _remain - len(cursms)
        sms.append(cursms)

    print 'gotSMS: ' + str(gotSMS)
    # return flag
    return gotSMS

def processSMS(sms, sm):

    # lower text the message so we can parse it
    # anoying the iPhone capitalising first char
    _lowertxt = sms[0]['Text'].lower()
 
    # some vars
    _sentDebug = None
    _understoodSms = False

    # might have debug in it
    # do this first to trap lots of lovely debug
    if 'debug' in _lowertxt:
        print 'SMS txt had debug in it: ' + sms[0]['Text']
        _sentDebug = debugSMS(sms, sm)
        _understoodSms = True

    print 'We should get this far...'

    # might be a phone set command
    if 'update phone' in _lowertxt:
        print 'SMS txt had update phone in it: ' + sms[0]['Text']
        _sentDebug = updatePhoneSms(sms, sm)
        _understoodSms = True

    # might be an anchor alarm off
    if 'anchor alarm off' in _lowertxt:
        print 'SMS txt had set anchor alarm off in it: ' + sms[0]['Text']
        _sentAnchorAlarmOffSms = anchorAlarmOffSms(sms, sm)
        _understoodSms = True

    # might be a config message
    if 'config' in _lowertxt:
        print 'SMS txt had config in it: ' + sms[0]['Text']
        configSms(sms, sm)
        _understoodSms = True

    # set the anchor alarm
    if 'set anchor alarm' in _lowertxt:
        print 'SMS txt had set anchor alarm in it: ' + sms[0]['Text']
        setAnchorAlarmSms(sms, sm)
        _understoodSms = True

    if 'set regular status' in _lowertxt:
        print 'SMS txt had set regular status' + sms[0]['Text']
        setRegularStatusSms(sms, sm)
        _understoodSms = True

    if 'regular status off' in _lowertxt:
        print 'SMS txt had regular status off' + sms[0]['Text']
        regularStatusOffSms(sms, sm)
        _understoodSms = True

    if 'send instructions' in _lowertxt:
        print 'SMS txt had send instructions in it: ' + sms[0]['Text']
        sendInstructionsSms(sms, sm)
        _understoodSms = True

    # send a status txt
    if 'send state' in _lowertxt:
        print 'SMS txt had send state: ' + sms[0]['Text']
        sendStateSms(sms, sm)
        _understoodSms = True

    # no idea what the SMS is...
    if _understoodSms is False:
        print 'No idea what that SMS was... ignoring: ' + sms[0]['Text']

    # finished!

def setRegularStatusSms(sms, sm):

    # get the number
    number = str(sms[0]['Number'])
    _lowertxt = sms[0]['Text'].lower()
    reply = None

    # fish out the global var
    global regularStatus

    results = re.search("set regular status (\d+)UTC", _lowertxt)

    # if we have a match
    if results:

        regularStatus = results.group(1)
        
        # save the config for next checks
        saveConfig()

        # sort a message to send back
        reply = boatname + ': Regular status setup to be sent around: ' + str(regularStatus) + 'UTC each day'

    else:
        # could not parse results
        reply = boatname + ': Regular status setup - could not parse: ' + str(_lowertxt)

    # sent the SMS
    sendSMS(number, reply, sm)

def regularStatusOffSms(sms, sm):

    # get the number
    number = str(sms[0]['Number'])
    reply = None

    # disabled the Alarm by Nulling the values
    regularStatus = 0

    # save the config for next checks
    saveConfig()

    # sort a message to send back
    reply = boatname + ': Regular status SMS being disabled!'

    # sent the SMS
    sendSMS(number, reply, sm)

def sendInstructionsSms(sms, sm):

    # get the number
    number = str(sms[0]['Number'])

    # Put are reply together
    reply = boatname + ': Commands:\nupdate phone NUMBER\nregular status TIMEUTC\nregular status off\nset anchor alarm DISTANCEINM\nanchor alarm off\ndebug\nsend state'

    # sent the SMS
    sendSMS(number, reply, sm)

def checkRegularSatus(sm):

   global phone
   global regularStatus

   if regularStatus != '':
       # and time is past that time UTC
       # and not sent today (check file)

       # prepare reply
       reply = boatname + ': Regular status at ' + regularStatus + ' UTC: ' + getSatus()

       # send it
       sendSMS(phone, reply, sm)

   else:
       print 'regularSatus not set'

def getSatus():

   _status = ''
   print 'Getting regular status'

   _status = 'Status is ... FAB'

   # return what we have
   return _status

def sendStateSms(sms, sm):

    # get the number
    number = str(sms[0]['Number'])
    reply = None

    # get status and sort message to send back
    reply = boatname + ': ' + getSatus()

    # sent the SMS
    sendSMS(number, reply, sm)

def anchorAlarmOffSms(sms, sm):

    # get the number
    number = str(sms[0]['Number'])
    reply = None

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
    reply = boatname + ': Anchor alarm being diabled!'
            
    # sent the SMS
    sendSMS(number, reply, sm)

def debugSms(sms, sm):

    # either put debug on/off
    _lowertxt = sms[0]['Text'].lower()

    # setup reply
    reply = None
    sent = None

    # set global var
    global debug

    if 'true' in _lowertxt:
        debug = True
        reply = boatname + ': Setting debug to True'
    elif 'off' in _lowertxt:
        debug = False
        reply = boatname + ': Setting debug to False'
    else:
        print 'Not idea what that was ... not changing anything'
        reply = boatname + ': Could not parse debug message : ' + _lowertxt

    # send message back to number that did the sending
    number = str(sms[0]['Number'])
    # setup the reply text
    print 'Reply: ' + reply + ', to: ' + sms[0]['Number']
    # send it
    sent = sendSMS(number, reply, sm)
    return sent

def saveConfig():

    print 'saveconfig'

    #
    # Need to save the following...
    # configs to save
    # 'debug', 'gpsFixTimeout', 'phone', 'boatname', 'wakeInNSecs', 'numberGpsFixesToAverage', 'lat', 'lon', 'alarmRange'

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
    configP.set('main', 'numberGpsFixesToAverage', str(numberGpsFixesToAverage))
    configP.set('main', 'gpsFixTimeout', str(gpsFixTimeout))

    # Print to stdout
    configP.write(sys.stdout)

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
    global gpsFixTimeout
    global regularStatus
    global numberGpsFixesToAverage

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
        gpsFixTimeout = configP.getint('main', 'gpsFixTimeout')
    except:
        # default to 60 tries
        gpsFixTimeout = int(60)

    try:
        numberGpsFixesToAverage = configP.getint('numberGpsFixesToAverage')
    except:
        # default to 10
        gpsFixTimeout = int(10)

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

    print 'debug is: ' + str(debug)
    print 'lat is: ' + str(lat)
    print 'lon is: ' + str(lon)
    print 'boatname is: ' +str(boatname)
    print 'phone is: ' +str(phone)
    print 'alarmRange is: ' + str(alarmRange)
    print 'wakeInNSecs is: ' + str(wakeInNSecs)
    print 'gpsFixTimeout is: ' + str(gpsFixTimeout)
    print 'regularStatus is: ' + str(regularStatus)
    print 'numberGpsFixesToAverage is: ' +str (numberGpsFixesToAverage)

def setAnchorAlarmSms(sms, sm):

    # lower case the message
    _lowertxt = sms[0]['Text'].lower()
    # get the number
    number = str(sms[0]['Number'])
    reply = None
    _newRange = None

    # where are we
    _fixStatus, _lat, _lon, _speed, _heading = gpsfix()

    # setglobal vars
    global lat
    lat = _lat 
    global lon
    lon = _lon
    global alarmRange

    # lookfing for string like
    # set anchor alarm 100m or
    # set anchor alarm

    # parse the SMS for alarm range
    results = re.search("set anchor alarm (\d+)m", _lowertxt)
    if results:
        _newRange = results.group(1)

    if _newRange > 1:

        # so should have something sensible to set the alarmRange to
        alarmRange = _newRange

    else:
        # zeros sent?  Do not reset alarmRange
        print 'Not positive digits in alarmRange, using 100M: ', _lowertxt

        # if not set to default 100M
        if not alarmRange:
            alarmRange = 100

    # Ok, got this far, should have something sensible to do

    # save the config for next checks
    saveConfig()
            
    # sort a message to send back
    reply = boatname + ': Anchor alarm being set for LAT: ' + str(_lat) 
    + ', LON: ' + str(_lon) + ', Alarm range: ' + str(alarmRange)
            
    # sent the SMS
    sendSMS(number, reply, sm)

def updatePhoneSms(sms, sm):

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
    
        # so should have something sensible to set the alarmRange to
        oldphone = phone
        phone = _newPhone

        # got this far, should have something sensible to set

        # save the config for next checks
        saveConfig()

        # sort a message to reply back letting original phone know of reset
        reply = boatname + ': New phone being set: ' + str(phone) + '.  To reset the phone back to this phone, reply to this SMS with:\n\nupdate phone ' + str(oldphone)

        # sent the reply SMS
        sendSMS(number, reply, sm)

        if phone != number:
            # send message to the new phone
            reply = boatname + ': New phone being set: ' + str(phone) + '.  to reset the phone back to old phone, reply to this SMS with:\n\nupdate phone ' + str(oldphone)
            # sent the reply SMS
            sendSMS(phone, reply, sm)
 
    else:
        # zeros sent?  Do not reset phone
        print 'Not a phone positive digits in: ', _lowertxt

def configSms(sms, sm):

    _lowertxt = sms[0]['Text'].lower()
    reply = None
    minutes = None
    global wakeInNSecs
    global boatname   
 
    #print "Location:%s\t State:%s\t Folder:%s\t Text:%s" % (sms[0]['Location'],sms[0]['State'],sms[0]['Folder'],sms[0]['Text'])
    #print sms
    print 'Doing config'
    print 'From: ' + sms[0]['Number']
    print 'Config message: ' + sms[0]['Text']

    # lookfing for strings like

    # check for config wake NUM
    if 'wake' in _lowertxt:

        # setup regex
        results = re.search("config wake (\d+)", _lowertxt)

        # check it matched
        if results:

            # fish out the first glob
            minutes = results.group(1)

            # if not less than 1!
            if minutes > 1:

                # make it seconds from (assumed minutes)
                wakeInNSecs = int(minutes) * 60

                # create a reply
                reply = boatname + ': setting wakeInNSecs to: ' +  str(wakeInNSecs)

                # find the number
                number = str(sms[0]['Number'])

                # send the SMS
                sendSMS(number, reply, sm)

            # less than one?  Zeros?
            else:
                print 'Not positive digits in: ', _lowertxt

        # no regex match
        else:
            print 'No regex match in: ', _lowertxt

    # check for config boatname
    if 'config boatname' in _lowertxt:
 
        # setup regex
        results = re.search('boatname (.+)$', sms[0]['Text'])

        # check it matched...
        if results:

            # fish out the first group
            boatname = results.group(1)

            # and if it is not null change config and send sms
            if boatname:

                # save the config for next checks
                saveConfig()

                # stick reply together
                reply = boatname + ': Resetting boatname to: ' + str(boatname)

                # get the number
                number = str(sms[0]['Number'])

                # send the sms
                sendSMS(number, reply, sm)

        # must have gone wrong
        else:
            print 'Confused on setting boatname: ', _lowertxt

    # got confused ...
    else:
        print 'Could not parse: ', _lowertxt

def smsFix(sm):

    # get a fix and send an SMS

    # get a fix
    fixStatus, lat, lon, speed, heading = gpsfix()

    # did stuff go bad?
    if fixStatus is 0:
        print 'Sorry, no GPS fix'
        message = boatname + ': NO GPS FIX'
    else:
        # so lets send a txt
        message = boatname + ': LAT: ' + str(lat) + ', LON: ' + str(lon) + ', SPEED :' + str(speed) + ', HEADING: ' + str(heading)

    # print out some data
    print 'Lat is: ', lat
    print 'Lon is: ', lon
    print 'Speed is: ', speed
    print 'Heading is: ', heading

    # so we know where we are, or it timed out

    if sendSMS(phone, message, sm) is False:
        print 'Oh my ... failed to send SMS'

def setUpGammu(sm):

    # setups the SMS gammu system
    # returns true if all good
    # return false if there are issues

    # create a state machine
    sm = gammu.StateMachine()
    
    # try and read the config
    try:
        print 'Going to read /home/pi/.gammurc config ...'
        sm.ReadConfig(Filename = '/home/pi/.gammurc') 

    except Exception as inst:
        print 'Pants failed ...'
        print type (inst)
        print inst

        # ok went bad - return false
        return False 
    print 'Read gammu /home/pi/.gammurc config'

    # Now call gammu init
    # this takes about 1 sec per go, and we are going to
    # try gammuInittries times
    _gammuInittries = 5
    _tries = 1    
    
    while True:
        print "We are on trying gammu Init() %d times" % (_tries)
        try:
            print 'Going to cal gammu Init() ...'
            sm.Init()
            print 'gammu Init() done in: ' + str(_tries)
            break 
        except Exception as inst:
            print 'Pants failed  ...'
            print type (inst)
            print inst 
            
        # got this far it might have failed
        _tries += 1
        time.sleep(2)
        
        # tried too many times
        if _tries >= _gammuInittries:
            print 'Pants tried: ' + str(_tries) + 'times to init Gammu.... it broke'
            return False

    print 'gammu init done'
    # got this far so must be good!
    return sm

def checkAnchorAlarm(sm):

   # if alarmRange is set, then check present position with old one
   # but do not reset the old position

   if alarmRange:

       # get fix
       fixStatus, newlat, newlon, speed, heading = gpsfix()
        
       # compare fix with saved config
       movedDistanceKm = distance(float(lat), float(lon), float(newlat), float(newlon))
       print 'Distance moved is: ' + str(movedDistanceKm)
       # change the distance to meters rounded (not 100% accurate)
       movedDistanceM = int(movedDistanceKm * 1000)

       # work out if less than alarmRange
       if movedDistanceM > alarmRange:
           # Oh - we seem to be outside the alarm range ...
           # Bleat
           message = boatname + ': ANCHOR ALARM FIRED.  Distance moved: ' + str(movedDistanceM) +'M, Alarm distrance set: ' + str(alarmRange) + 'M. Present position/heading LAT: ' + str(newlat) + ', LON: ' + str(newlon) + ', SPEED:' + str(speed) + ', HEADING: ' + str(heading)
           if sm:
               sendSMS(phone, message, sm)
       else:
           print 'Safe: distance moved is: ' + str(movedDistanceM) + 'M is less than alarmRange: ' + str(alarmRange) + 'M'

def distance(lat1, lon1, lat2, lon2):

    # stolen from https://github.com/sivel/speedtest-cli/blob/master/speedtest_cli.py
    """Determine distance between 2 sets of [lat,lon] in km"""

    #lat1, lon1 = origin
    #lat2, lon2 = destination
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2)) * math.sin(dlon / 2)
         * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d

def main():

    # started ...

    # global Objects
    sm = None
    configP = None

    loadConfig()
 
    print 'debug is: ' + str(debug)
    print 'lat is: ' + str(lat)
    print 'lon is: ' + str(lon)
    print 'boatname is: ' +str(boatname)
    print 'phone is: ' +str(phone)
    print 'alarmRange is: ' + str(alarmRange)
    print 'wakeInNSecs is: ' + str(wakeInNSecs)
    print 'gpsFixTimeout is: ' + str(gpsFixTimeout)
    print 'regularStatus is: ' + str(regularStatus)
    # lets get the modem up
    sm = setUpGammu(sm)
    print 'gammu init done'

    if sm:
        # we have a modem lets do some SMS checking
    #if sendSMS(phone, message, sm) is False:
    #    print 'Oh my ... failed to send SMS'

        if getSMS(sm) is False:
            print 'No SMS to process'
        else:
           print 'Got some SMS'

    # if we checked SMS and things like anchor alarm or debug are on
    # the go

    # get and record a fix

    # check the anchorAlarm
    if alarmRange > 1:
       if lat != '' and lon !='':
           checkAnchorAlarm(sm)
       else:
           print 'No Lat/Lon to compare to:  Ops.. lat: ' + str(lat) + ', lon: ' + str(lon) + ', alarmRange is: ' + str(alarmRange)
    else:
       print 'No Anchor alarm set'

    # check regularStatus
    if regularStatus > 1:
        checkRegularSatus(sm)

    #logger(getSatus())

if __name__ == '__main__':
    main()

# vim:ts=4:sw=4:expandtab
# cat /home/pi/.vimrc 
# syntax on
# filetype indent plugin on
# set modeline
