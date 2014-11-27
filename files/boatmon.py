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
gpsFixTimeout = 20
phone = ''
boatname = ''
debug = False
# gammu statemachine
sm = None
wakeInNSecs = ''
numberGpsFixesToAverage = 10
alarmRange = ''


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
    _sumLat = 0
    _sumLon = 0
    _sumSpeed = 0
    _sumHeading = 0

    while True:
        try:
            report = session.next()
            if report['class'] == 'TPV':

                _loop += 1
                #print 'GPS fix Loop is: ', _loop

                if ( hasattr(report, 'speed') and hasattr(report, 'lon') and hasattr(report, 'lat') and hasattr(report, 'track')):
                    # we got a fix... break
                    _sumLat = _sumLat + report.lat
                    _sumLon = _sumLon + report.lon
                    _sumSpeed = _sumSpeed + report.speed
                    _sumHeading = _sumHeading + report.track
                    #print 'Got a fix', _sumLat, report.lat, _sumLon, report.lon, _sumSpeed,  report.speed, _sumHeading, report.track, _loop
                    #break

                    # if we have enough data, calc average and break
                    if _loop == numberGpsFixesToAverage:
                        _lat = _sumLat / numberGpsFixesToAverage
                        _lon = _sumLon / numberGpsFixesToAverage
                        _speed = _sumSpeed / numberGpsFixesToAverage
                        _heading = _sumHeading / numberGpsFixesToAverage
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

    _remain = _status['SIMUsed'] + _status['PhoneUsed'] + _status['TemplatesUsed']
    print 'there are: ', _remain, 'sms to deal with'

    if _remain == 0:
        return False

    while _remain > 0:
        if _start:
            cursms = sm.GetNextSMS(Start = True, Folder = 0)
            _start = False
            #print 'Processing sms: ' + str(cursms)
            processSMS(cursms, sm)
            gotSMS += 1
        else:
            cursms = sm.GetNextSMS(Location = cursms[0]['Location'], Folder = 0)
            #print 'Processing sms: ' + str(cursms)
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

    if 'send state' in _lowertxt:
        print 'SMS txt had send state: ' + sms[0]['Text']
        sendStateSms(sms, sm)
        _understoodSms = True

    # no idea what the SMS is...
    if _understoodSms is False:
        print 'No idea what that SMS was... ignoring: ' + sms[0]['Text']

    # finished!

def sendStateSms(sms, sm):

    # get the number
    number = str(sms[0]['Number'])
    reply = None

    ##### go gate state.... ####

    # sort message to send back
    reply = boatname + ': State is fab...'

    # sent the SMS
    sendSMS(number, reply, sm)

def anchorAlarmOffSmsS(sms, sm):

    # get the number
    number = str(sms[0]['Number'])
    reply = None

    # disabled the Alarm by Nulling the values
    lat = None
    lon = None
 
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

    configP.set('main', 'debug', str(debug))
    configP.set('main', 'gpsFixTimeout', str(gpsFixTimeout))
    configP.set('main', 'wakeInNSecs', str(wakeInNSecs))

    if phone:
        configP.set('main', 'phone', str(phone))
    if boatname:
        configP.set('main', 'boatname', str(boatname))
    if lat:
        configP.set('main', 'lat', str(lat))
    if lon:
        configP.set('main', 'lon', str(lon))
    if alarmRange:
        configP.set('main', 'alarmRange', str(alarmRange))

    configP.write(sys.stdout)

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

    # setup the config system
    configP = ConfigParser.SafeConfigParser()
    configFileRead = configP.read(configFile)

    debug = configP.getboolean('main', 'debug')

    # may not be set
    try: 
        debug = configP.getboolean('main', 'debug')
        phone = configP.get('main', 'phone')
        boatname = configP.get('main', 'boatname')
        lat = configP.get('main', 'lat')
        lon = configP.get('main', 'lon')
        alarmRange = configP.getint('main', 'alarmRange')        

    except Exception:
        phone = ''
        boatname = ''
        lat = ''
        lon = ''
        alarmRange = ''

    wakeInNSecs = configP.getint('main', 'wakeInNSecs')
    gpsFixTimeout = configP.getint('main', 'gpsFixTimeout')

    print 'debug is: ' + str(debug)
    print 'lat is: ' + str(lat)
    print 'lon is: ' + str(lon)
    print 'boatname is: ' +str(boatname)
    print 'phone is: ' +str(phone)
    print 'alarmRange is: ' + str(alarmRange)
    print 'wakeInNSecs is: ' + str(wakeInNSecs)
    print 'gpsFixTimeout is: ' + str(gpsFixTimeout)

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
    reply = boatname + ': Anchor alarm being set for LAT: ' + str(_lat) + ', LON: ' + str(_lon) + ', Alarm range: ' + str(alarmRange)
            
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
      
       # change the distance to meters rounded (not 100% accurate)
       movedDistanceM = int(movedDistanceKm / 1000)

       # work out if less than alarmRange
       if movedDistanceM > alarmRange:
           # Oh - we seem to be outside the alarm range ...
           # Bleat
           message = boatname + ': ANCHOR ALARM FIRED.  Distance moved: ' + str(movedDistanceM) +'M, Alarm distrance set: ' + str(alarmRange) + 'M. Present position/heading LAT: ' + str(lat) + ', LON: ' + str(lon) + ', SPEED:' + str(speed) + ', HEADING: ' + str(heading)
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
           print 'No Lat/Lon to compare to:  Ops.. lat: ' + str(lat) + ', lon: ' + str(lon)
    else:
       print 'No Anchor alarm set'

if __name__ == '__main__':
    main()

# vim:ts=4:sw=4:expandtab
