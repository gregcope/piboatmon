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
        self.rollingTrack = 0
        self.rollingSpeed = 0
        self.rollingEpx = 0
        self.rollingEpy = 0
        self.rollingSatsUsed = 0
        self.rollingHdop = 0
        self.rollingWindow = window

        if self.rollingWindow < 3 or self.rollingWindow > 10:
            logging.error('Rolling average window needs to be between 3 or 10')

        # we are going to be a thread
        threading.Thread.__init__(self)

        logging.debug('Setting up gpspoller __init__ class with rolling Average window of: '
                      + str(self.rollingWindow))

        try:

            self.gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info

        except:

            logging.error('GPS thread Ops... gpsd not running right?'
                          + 'Hint: sudo /etc/init.d/gpsd start')

        self.running = False
        logging.debug('gpspoller __init__ finished')
 
    def run(self):

        self.running = True
        logging.info('gpspoller Running')

        # create the deques of the right length
        # but make them zero
        # we do not populat the rolling average
        # until we have the right number of results
        self.dLat = deque([0, 0, 0], self.rollingWindow)
        self.dLon = deque([0, 0, 0], self.rollingWindow)
        self.dTrack = deque([0, 0, 0], self.rollingWindow)
        self.dSpeed = deque([0, 0, 0], self.rollingWindow)
        self.dEpx = deque([0, 0, 0], self.rollingWindow)
        self.dEpy = deque([0, 0, 0], self.rollingWindow)
        self.dSatsUsed = deque([0, 0, 0], self.rollingWindow)
        self.dHdop = deque([0, 0, 0], self.rollingWindow)

        while self.running:

            try:

                # this will continue to loop 
                # and grab EACH set of gpsd info 
                # to clear the buffer
                self.gpsd.next()

                # check if we have a good fix
                if str(self.gpsd.fix.mode) == '3':

                    logging.info('GPS 3D fix! lat: '
                                 + str(self.gpsd.fix.latitude) + ', lon: '
                                 + str(self.gpsd.fix.longitude) + ', stats: '
                                 + str(self.gpsd.satellites_used) + ', hdop: '
                                 + str(self.gpsd.hdop) )

                    self.num3DFixes += 1

                    # add good fix info to the fix disque
                    self.dLat.append(self.gpsd.fix.latitude)
                    self.dLon.append(self.gpsd.fix.longitude)
                    self.dTrack.append(self.gpsd.fix.track)
                    self.dSpeed.append(self.gpsd.fix.speed)
                    self.dEpx.append(self.gpsd.fix.epx)
                    self.dEpy.append(self.gpsd.fix.epy)
                    self.dSatsUsed.append(self.gpsd.satellites_used)
                    self.dHdop.append(self.gpsd.hdop)

                if self.num3DFixes >= self.rollingWindow:

                    # should have enough good Lat/Lons,
                    # so we can average and populate the rolling lat/lon

                    logging.info('Updating rolling average')

                    self.rollingLat = self.movingAverage(self.dLat)
                    self.rollingLon = self.movingAverage(self.dLon)
                    self.rollingTrack = self.movingAverage(self.dTrack)
                    self.rollingSpeed = self.movingAverage(self.dSpeed)
                    self.rollingEpx = self.movingAverage(self.dEpx)
                    self.rollingEpy = self.movingAverage(self.dEpy)
                    self.rollingSatsUsed = self.movingAverage(self.dSatsUsed)
                    self.rollingHdop = self.movingAverage(self.dHdop)
 
            except StopIteration:
                self.gpsd = None
                logging.error('GPS thread GPSD has terminated')

    def stop(self):

        self.running = False
        logging.info('Stopping gps thread')


    def movingAverage(self, data):

        total = 0

        for n in range(len(data)):
            total += data[n]

        return total / len(data)


    def getCurrentRollingAvData(self):

        if self.num3DFixes < self.rollingWindow:
            logging.warn('Calling rolling average with no enough 3D fixes - num3DFixes: '
                         + str(self.num3DFixes) + ', rollingWindow: ' 
                         + str(self.rollingWindow) )
            return 1000

        return (self.num3DFixes,
                self.rollingLat,
                self.rollingLon,
                self.rollingTrack,
                self.rollingSpeed,
                self.rollingEpx,
                self.rollingEpy,
                self.rollingSatsUsed,
                self.rollingHdop)
                
# print gps.misc.EarthDistance((51,0),(51.00008945,0)) 
# http://fossies.org/dox/gpsd-3.11/gps_8py_source.html
