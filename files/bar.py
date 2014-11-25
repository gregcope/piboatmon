import ConfigParser
import sys
#from ConfigParser import SafeConfigParser

configFile = "/home/pi/rpi/files/boatmon.config"

Config = ConfigParser.SafeConfigParser()
configFileRead = Config.read(configFile)

if configFileRead:
    print 'Read config files: ', configFileRead
#else:
#    print 'Could not read: ', configFile 


gpsFixTimeout = Config.getint('main', 'gpsFixTimeout')

print 'gpsFixTimeout is', gpsFixTimeout

gpsFixTimeout = 33
print 'gpsFixTimeout is', gpsFixTimeout

Config.write(sys.stdout)

print
print 'About to save'
print 

Config.set('main', 'gpsFixTimeout', str(gpsFixTimeout))

print
Config.write(sys.stdout)

with open(configFile, 'w') as configFilehandle:
    Config.write(configFilehandle)
