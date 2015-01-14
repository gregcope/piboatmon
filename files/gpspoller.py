from gps import *
import threading
import logging
import time

# http://www.danmandle.com/blog/getting-gpsd-to-work-with-python/

class gpspoller(threading.Thread):

    def __init__(self):

        self.gpsd = None
        self.foo = None

        # we are going to be a thread
        threading.Thread.__init__(self)

        logging.debug('Setting up gpspoller __init__ class')

        try:

        self.gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info

        except:

            logging.error('GPS thread Ops... gpsd not running right?'
                          + 'Hint: sudo /etc/init.d/gpsd start')

        self.running = True #setting the thread running to true
        print 'started'
 
    def run(self):

        while self.running:

            print 'Foo'
            #try:
            #    self.gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer
            #except StopIteration:
            #    self.gpsd = None
            #    logging.error('GPS thread GPSD has terminated')

    def getCurrentAvgData(self):

        print self.gpsd.fix.latitude
        print self.gpsd.fix.longitude
        print self.gpsd.satellites
