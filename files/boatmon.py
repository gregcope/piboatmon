#!/usr/bin/python

"""
Python script to check stuff then send and SMS
"""

import gps
import time
import gammu
import re

# some defaults
lat = 51.013648333
lon = -0.449681667
# has to be more than numberGpsFixesToAverage
gpsFixTimeout = 20
phone = '07769907533'
boatname = 'pi'
debug = False
# gammu statemachine
sm = None
wakeInNSecs = 1800
numberGpsFixesToAverage = 10

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
    print 'Sending txt:' + txt + ', to: ' + phone

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
    except:
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
    # might be a config message
    if 'config' in _lowertxt:
        print 'SMS txt had config in it: ' + sms[0]['Text']
        configSMS(sms, sm)
        _understoodSms = True

    # set the anchor alarm
    if 'anchor alarm set' in _lowertxt:
        print 'SMS txt had set anchor alarm in it: ' + sms[0]['Text']
        setAnchorAlarm(sms, sm)
        _understoodSms = True

    # no idea what the SMS is...
    if _understoodSms is False:
        print 'No idea what that SMS was... ignoring: ' + sms[0]['Text']

    # finished!

def debugSMS(sms, sm):

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

def saveconfig():

    print 'saveconfig' 

def setAnchorAlarm(sms, sm):

    # lower case the message
    lowertxt = sms[0]['Text'].lower()
    number = str(sms[0]['Number'])
    reply = None
    
    # where are we
    _fixStatus, _lat, _lon, _speed, _heading = gpsfix()

    # setglobal vars
    global lat
    lat = _lat 
    global lon
    lon = _lon

    # save config
    saveconfig()

    # sort a message to send back
    reply = boatname + ': Anchor alarm being set for LAT: ' + str(_lat) + ', LON: ' + str(_lon)

    # send the reply
    sendSMS(number, reply, sm)

def configSMS(sms, sm):

    lowertxt = sms[0]['Text'].lower()
    mins = None
    reply = None
    minutes = None
    
    #print "Location:%s\t State:%s\t Folder:%s\t Text:%s" % (sms[0]['Location'],sms[0]['State'],sms[0]['Folder'],sms[0]['Text'])
    #print sms
    print 'Doing config'
    print 'From: ' + sms[0]['Number']
    print 'Config message: ' + lowertxt

    # lookfing for string like
    # config wake NUM
    if 'wake' in sms[0]['Text']:
        mins = re.search("config wake (\d+)", lowertxt)
        global wakeInNSecs
        reply = boatname + ': wakeInNSecs was: ' + str(wakeInNSecs)
        minutes = mins.group(1)
        if minutes > 1:
            wakeInNSecs = int(minutes) * 60
            reply = reply + ', wakeInNSecs now: ' +  str(wakeInNSecs)
            number = str(sms[0]['Number'])
            sendSMS(number, reply, sm)
        else:
            # zeros sent?
            print 'Not positive digits in: ', lowertxt
    else:
        print 'Could not parse: ', lowertxt

def main():

    debug = False
    # started ...
    print "running, wakeInNSecs is: ", wakeInNSecs, ", debug is: ", debug

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

    # lets get the modem up
    sm = gammu.StateMachine()

    try:
        print 'Going to read /home/pi/.gammurc config ...'
        sm.ReadConfig(Filename = '/home/pi/.gammurc')
    except Exception as inst:
        print 'Pants failed ...'
        print type (inst)
        print inst
    print 'Read gammu /home/pi/.gammurc config'
 
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
            exit (1)

    print 'gammu init done'

    #if sendSMS(phone, message, sm) is False:
    #    print 'Oh my ... failed to send SMS'

    if getSMS(sm) is False:
        print 'No SMS to process'
    else:
        print 'Got some SMS'

    # so now DEBUG might be on and we might want to delay reboot
    print "Stopping, wakeInNSecs is: ", wakeInNSecs, ", debug is: ", debug

if __name__ == '__main__':
    main()

# vim:ts=4:sw=4:expandtab
