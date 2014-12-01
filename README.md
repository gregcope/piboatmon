rpi
===

A system to turn a Raspberry PI into a boat monitoring solution.  It is configured by Puppet and then runs a Python script that

1. Reads config
2. Starts a GPS thread logging GPS positions
3. Checks for inbound SMS messages from a 3G USB modem
4. Checks the anchor Alarm
5. Logs present status
6. Checks to see if it needs to send a status SMS
7. Goes to sleep for wakeInNSecs
8. Rinse/repeat

How it works
------------

* It is based on a Rasberry PI with a stripped down Rasbian image.
* Uses a PI Model A+ for size, cost and low power
* Uses an Adafruit Ultimate GPS connected to the PI reconfigured UART
* Uses a 3G USB modem to send/receive SMS messages
* Uses a mopi to sleep/wake, get battery Volts and have backup power
* Is mostly writen in Python with a bit of shell
* (TBC) Will act on a bilge float switch going off to warn of rising Bilge levels 
* Puppet is used to configure the host and install all the needed packages and configure the services

Configuration
-------------

The Python script is configured in two ways;

1. By a confuration file `boatmon.config`
2. By sending the SMS number configuration messages

### Config Script

The python script uses a config file called `boatmon.config` which looks like:
```[main]
debug = True
gpsfixtimeout = 10
wakeinnsecs = 1800
lat = 
lon = 
alarmrange = 0
phone = 
boatname = <not set>
regularstatus = 0
```

### Config SMS

The system understands the following config SMS

* `set boatname NAME` - Sets the boatname prefix to SMS messages
* `nupdate phone NUMBER` - Sets the phone number to send messages to
* `regular status TIMEUTC` - Sets a regular status SMS message 
* `regular status off` - Stops the regular status SMS messages
* `set anchor alarm DISTANCEINM` - Sets the anchor alarm (records the fix) and sets the distance given as the alarm range.  If no distance given defaults to 100M
* `anchor alarm off` - Stops the anchor alarm tracking / SMS messages
* `debug` - Enables Debuging (dev use only)
* `send state` - Will reply with a status SMS
* `send instructions` - Sends a short instructions SMS (edited version of this)
