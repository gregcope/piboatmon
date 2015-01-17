from __future__ import division
from collections import deque
import numpy as np
from gps import *
import threading
import logging
import time

# http://sentdex.com/sentiment-analysisbig-data-and-python-tutorials-algorithmic-trading/how-to-chart-stocks-and-forex-doing-your-own-financial-charting/calculate-simple-moving-average-sma-python/
# http://www.danmandle.com/blog/getting-gpsd-to-work-with-python/
# http://www.stuffaboutcode.com/2013/09/raspberry-pi-gps-setup-and-python.html

class gpspoller(threading.Thread):

    def __init__(self):

        self.gpsd = None
        self.num3DFixes = 0
        self.rollingLat = 0
        self.rollingLon = 0
        self.rollingWindow = 3

        # we are going to be a thread
        threading.Thread.__init__(self)

        logging.debug('Setting up gpspoller __init__ class')

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
        self._dLat = deque([0, 0, 0], self.rollingWindow)
        self._dLon = deque([0, 0, 0], self.rollingWindow)

        while self.running:

            try:

                #this will continue to loop and grab EACH set of gpsd info to clear the buffer
                self.gpsd.next()

                if str(self.gpsd.fix.mode) == '3':
                    self.num3DFixes += 1

                    self.dLat.append(self.gpsd.fix.latitude)
                    self.dLon.append(self.gpsd.fix.lontitude)

                if self.num3DFixes >= self.rollingWindow:

                    # should have enough good Lat/Lons,
                    # so we can average and populate the rolling lat/lon

                    self.rollingLat = movingAverage(self.dLat)
                    self.rollingLon = movingAverage(self.dLon)
 
            except StopIteration:
                self.gpsd = None
                logging.error('GPS thread GPSD has terminated')

    def stop(self):

        self.running = False


    def movingAverage(data):

        total = 0

        for n in range(len(data)):
            total += data[n]

        return total / len(data)


    def getCurrentRollingAvData(self):

        if self.num3DFixes < 3:
            return -1

        # should be good ... to start the rolling average
        rollingAverage(self.dLat)
        

        print self.num3DFixes
        _fixesAtStart = self.num3DFixes

        while self.num3DFixes < _fixesAtStart + 3:
            if self.num3DFixes == 1:
                time.sleep(1)
                print 'Skipping - no fix'
                next

            print _fixesAtStart
            print self.num3DFixes
            time.sleep(1)

    def getFix(self):

        print self.num3DFixes
        print self.gpsd.status
        # 1 = NO_FIX, 2 = FIX, 3 = DGPS_FIX
        print self.gpsd.fix.mode
        # 0 = ZERO, 1 = NO_FIX, 2 = 2D, 3 = 3D
        print self.gpsd.fix.latitude
        print self.gpsd.fix.longitude
        print self.gpsd.fix.epy
        print self.gpsd.fix.epx
        print self.gpsd.satellites_used
        print self.gpsd.pdop 

#print gps.misc.EarthDistance((51,0),(51.00008945,0)) 
# http://fossies.org/dox/gpsd-3.11/gps_8py_source.html
