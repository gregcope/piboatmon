import gps
import threading
import logging

# http://www.danmandle.com/blog/getting-gpsd-to-work-with-python/

class gpspoller(threading.Thread):

    # class variables
    gpsd = None

    def __init__(self):

        # we are going to be a thread
        threading.Thread.__init__(self)

        logging.debug('Setting up gpspoller __init__ class')

        try:

            gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info

        except:
            logging.error('GPS thread Ops... gpsd not running right?'
                          + 'Hint: sudo /etc/init.d/gpsd start')

        self.current_value = None
        self.running = True #setting the thread running to true
 
    def run(self):

        while gpsp.running:

            try:
                gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer
            except StopIteration:
                gpsd = None
                logging.error('GPS thread GPSD has terminated')

    def getCurrentAvgData(self):

        print gpsd.fix.latitude
        print gpsd.fix.longitude
        print gpsd.satellites
