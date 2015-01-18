from __future__ import division
from collections import deque
import numpy as np
from gps import *
import threading
import logging
import time

# http://www.danmandle.com/blog/getting-gpsd-to-work-with-python/
# http://www.stuffaboutcode.com/2013/09/raspberry-pi-gps-setup-and-python.html

class gpspoller(threading.Thread):

    def __init__(self, window):

        self.gpsd = None
        self.num3DFixes = 0
        self.rollingLat = 0
        self.rollingLon = 0
        self.rollingWindow = window

        if self.rollingWindow < 3 or > 10:
            logging.error('Rolling average window needs to be between 3 or 10')

        # we are going to be a thread
        threading.Thread.__init__(self)

        logging.debug('Setting up gpspoller __init__ class with rolling Average window of: '
                      + str(self.rollingWindow))

        print 'Window is: ' + str(self.rollingWindow)

        try:

            self.gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info

        except:

            logging.error('GPS thread Ops... gpsd not running right?'
                          + 'Hint: sudo /etc/init.d/gpsd start')

        self.running = False 
        print 'started'
 
    def run(self):

        self.running = True

        # create the deques of the right length
        # but make them zero
        # we do not populat the rolling average
        # until we have the right number of results
        self.dLat = deque([0, 0, 0], self.rollingWindow)
        self.dLon = deque([0, 0, 0], self.rollingWindow)

        while self.running:

            try:

                # this will continue to loop 
                # and grab EACH set of gpsd info 
                # to clear the buffer
                self.gpsd.next()

                # check if we have a good fix
                if str(self.gpsd.fix.mode) == '3':

                    print '3D fix, adding to dLat: ' + str(self.gpsd.fix.latitude)
                    print '3D fix, adding to dLon: ' + str(self.gpsd.fix.longitude)
                    self.num3DFixes += 1

                    # add good fix info to the fix disque
                    self.dLat.append(self.gpsd.fix.latitude)
                    self.dLon.append(self.gpsd.fix.longitude)

                if self.num3DFixes >= self.rollingWindow:

                    # should have enough good Lat/Lons,
                    # so we can average and populate the rolling lat/lon

                    print 'Num 3D fixes' + str(self.num3DFixes) + ', greater than rolling window; ' + str(self.rollingWindow)
                    self.rollingLat = movingAverage(self.dLat)
                    self.rollingLon = movingAverage(self.dLon)
 
            except StopIteration:
                self.gpsd = None
                logging.error('GPS thread GPSD has terminated')

    def stop(self):

        self.running = False


    def movingAverage(self, data):

        total = 0

        for n in range(len(data)):
            print 'Averaging: ' + str(data[n])
            total += data[n]

        return total / len(data)


    def getCurrentRollingAvData(self):

        if self.num3DFixes < 3:
            return 1000

        print self.num3DFixes
        print self.gpsd.status
        # 1 = NO_FIX, 2 = FIX, 3 = DGPS_FIX
        print self.gpsd.fix.mode
        # 0 = ZERO, 1 = NO_FIX, 2 = 2D, 3 = 3D
        print self.gpsd.fix.latitude
        print self.gpsd.fix.longitude
        print self.rollingLat
        print self.rollingLon
        print self.gpsd.fix.epy
        print self.gpsd.fix.epx
        print self.gpsd.satellites_used
        print self.gpsd.pdop 

#print gps.misc.EarthDistance((51,0),(51.00008945,0)) 
# http://fossies.org/dox/gpsd-3.11/gps_8py_source.html
