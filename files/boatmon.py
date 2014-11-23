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
gpsFixTimeout = 10
phone = '07769907533'
boatname = 'pi'
debug = False
# gammu statemachine
sm = None
wake = 1800

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
    while True:
        try:
            report = session.next()
            if report['class'] == 'TPV':

                print 'GPS fix Loop is: ', _loop
                _loop += 1

                if ( hasattr(report, 'speed') and hasattr(report, 'lon') and hasattr(report, 'lat') and hasattr(report, 'track')):
                    # we got a fix... break
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
       return (0, 0, 0, 0, 0)

    # all good
    return (1, report.lat, report.lon, report.speed, report.track)

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

    # set this to nothing
    sms = None

    # get SMS message for this number
    gotSMS = False

    try:
        print 'GetSMSStatus() ...'
        sm.GetSMSStatus()
        print 'Done'
    except:
        print 'Pants failed to get SMSStatus ...'
        print type (inst)
        print inst

    print 'there are: ', sm.GetSMSStatus(), 'sms to deal with'

    _start = True
    while 1:
        # print 'In while, _start is: ' + str(_start)
        try :
            if _start:
                print 'in if bit'
                sms = sm.GetNextSMS(Start = True, Folder=0)
                print sms
                _start = False
            else:
                print sms
                print 'in else bit'
                #be careful sometimes Location is directly in the hash so you'll have to remove the [0]
                sms = sm.GetNextSMS(Location = sms[0]['Location'], Folder=0)
        except gammu.ERR_EMPTY:
            break

        # process them one at a time
        print 'Processing sms: ' + str(sms)
        processSMS(sms, sm)

        # set flag to true
        gotSMS = True

    print 'gotSMS: ' + str(gotSMS)
    # return flag
    return gotSMS

def processSMS(sms, sm):

    # process SMS'es
    # print "Location:%s\t State:%s\t Folder:%s\t Text:%s" % (sms[0]['Location'],sms[0]['State'],sms[0]['Folder'],sms[0]['Text'])

    #txt = sms[0]['Text']
    #lowertxt = txt.lower()
    lowertxt = sms[0]['Text'].lower()
    print
    print 'lowertxt is: ', lowertxt
    print 
    # might be a config message
    if 'config' in lowertxt:
        print 'SMS txt had config in it: ' + sms[0]['Text']
        configSMS(sms, sm)

    # might have debug in it
    elif 'debug' in lowertxt:
        print 'SMS txt had debug in it: ' + sms[0]['Text']
        debugSMS(sms, sm)

    # no idea what the SMS is...
    else:
        print 'No idea what that SMS was... ignoring: ' + sms[0]['Text']

    print 'About to delete sms'
    sm.DeleteSMS(Location = sms[0]['Location'], Folder = 1)

def debugSMS(sms, sm):

    # either put debug on/off
    _lowertxt = sms[0]['Text'].lower()
    reply = ''
    if 'true' in _lowertxt:
        debug = True
        reply = boatname + ': Setting debug to True'
    elif 'off' in _lowertxt:
        debug = False
        reply = boatname + ': Setting debug to False'
    else:
        print 'Not idea what that was ... not changing anything'
        reply = boatname + ': Could not parse debug message : ' + _lowertxt

    # send message back
    number = str(sms[0]['Number'])
    print 'Reply: ' + reply + ', to: ' + sms[0]['Number']
    sendSMS(number, reply, sm)

def configSMS(sms, sm):

    lowertxt = sms[0]['Text'].lower()
    #print "Location:%s\t State:%s\t Folder:%s\t Text:%s" % (sms[0]['Location'],sms[0]['State'],sms[0]['Folder'],sms[0]['Text'])
    #print sms
    print 'Doing config'
    print 'From: ' + sms[0]['Number']
    print 'Config message: ' + lowertxt

    # lookfing for string like
    # config wake NUM
    #if 'wake' in sms[0]['Text']:

def main():

    # started ...
    print "running"

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

if __name__ == '__main__':
    main()

# vim:ts=4:sw=4:expandtab
