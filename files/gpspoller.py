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
import logging

class gpspoller(threading.Thread):

    # class variables
    avLat = 0
    avLon = 0
    avSpeed = 0
    avHeading = 0
    avEpx = 0
    avEpy = 0
    numFixes = 0
    gpsd = None

    def __init__(self):

        # we are going to be a thread
        threading.Thread.__init__(self)

        if debug is True:
            logging.debug('Setting up gpspoller __init__ class')

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
        #global gpsd

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
                    #if debug is True:
                    logging.info('GPS thread report is ' + str(report))

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
                        _loop +=1

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
                            logging.debug('GPS thread stats: LAT '
                                          + str(self.avLat) + ' LON '
                                          + str(self.avLon) + ' VEL '
                                          + str(self.avSpeed) + ' HEAD '
                                          + str(self.avHeading) + 'T LAT +/- '
                                          + str(self.avEpx) + ' LON +/- '
                                          + str(self.avEpy) + ' No. fixes '
                                          + str(self.numFixes))

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

        # if EP is low
        if roundedEp > 15:

            # prefix poor fix
            prefix = prefix + 'POOR EP '

        if self.numFixes < 10:

            prefix = prefix + 'LOW no. fixes '

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


# create a gpsPollerthread and asks it to start
# gpsp = GpsPoller()
# gpsp.start()

# do some stuff

# gpsp.running = False
# gpsp.join()  # wait for the thread to finish what it's doing
