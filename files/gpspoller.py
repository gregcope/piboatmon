from gps import *
import threading
import logging
import time

# http://www.danmandle.com/blog/getting-gpsd-to-work-with-python/

class gpspoller(threading.Thread):

    def __init__(self):

        self.gpsd = None

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

        while self.running:

            try:
                self.gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer

                print self.gpsd.fix.mode

                if str(self.gpsd.fix.mode) == '3':
                    print "got a 3"
                
            except StopIteration:
                self.gpsd = None
                logging.error('GPS thread GPSD has terminated')

    def stop(self):

        self.running = False

    def getCurrentAvgData(self):

        print self.gpsd.fix.mode
        print self.gpsd.fix.latitude
        print self.gpsd.fix.longitude
        print self.gpsd.fix.epy
        print self.gpsd.fix.epx
        print self.gpsd.satellites_used
