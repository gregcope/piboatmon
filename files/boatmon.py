#!/usr/bin/python

"""
Python script to check stuff then send and SMS
"""

import gps
import time
import gammu

# some defaults
lat = 51.013648333
lon = -0.449681667
gpsFixTimeout = 1
phone = '07769907533'
boatname = 'Spindrift'
debug = False
# gammu statemachine
sm = None

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

                print 'Loop is: ', _loop
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
    message = {
        'Text': txt,
        'SMSC': {'Location': 1},
        'Number': phoneNum,
    }

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
        print 'Sent is: ' + str(sent)
    print 'returning sent = ', str(sent)
    return sent

def getSMS(sm):

    # get SMS message for this number
    # and if successful delete them...

    sm.GetSMSStatus() 
    print 'there are: ', sm.GetSMSStatus(), 'sms to deal with'

    remainSMS = status['SIMUsed'] + status['PhoneUsed'] + status['TemplatesUsed']
    sms = [] 
    start = True

    while remainSMS > 0:
        if start:
            curSMS = sm.GetNextSMS(Start = True, Folder=0)
            start = False
        else:
            cursms = sm.GetNextSMS(Location = curSMS[0]['Location'], Folder = 0)
        remainSMS = remainSMS - len(curSMS)
        sms.append(curSMS)

    print sms

    return False

def main():

    # started ...
    print "running"

    # get a fix
    fixStatus, lat, lon, speed, heading = gpsfix()

    # did stuff go bad?
    if fixStatus is 0:
        print 'Sorry, no GPS fix'

    # print out some data
    print 'Lat is: ', lat
    print 'Lon is: ', lon
    print 'Speed is: ', speed
    print 'Heading is: ', heading

    # so we know where we are, or it timed out

    # so lets send a txt
    message = boatname + ': LAT: ' + str(lat) + ', LON: ' + str(lon) + ', SPEED :' + str(speed) + ', HEADING: ' + str(heading)

    sm = gammu.StateMachine()

    try:
        print 'Going to read /home/pi/.gammurc config ...'
        sm.ReadConfig(Filename = '/home/pi/.gammurc')
    except Exception as inst:
        print 'Pants failed ...'
        print type (inst)
        print inst
    print 'Read gammu /home/pi/.gammurc config'
 
    # this takes about 1 sec ... 
    try:
        print 'Going to cal gammu Init() ...'
        sm.Init()
    except Exception as inst:
        print 'Pants failed  ...'
        print type (inst)
        print inst
    print 'gammu init done'

    if sendSMS(phone, message, sm) is False:
        print 'Oh my ... failed to send SMS'

    if getSMS(sm) is False:
        print 'Oh my ... failed to get sms'

if __name__ == '__main__':
    main()

# vim:ts=4:sw=4:expandtab
