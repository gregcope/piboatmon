PiBoatMon
===

A system to turn a Raspberry PI into a low power boat monitoring solution.  It is configured by Puppet and then runs a Python script that checks the systems like Bilge Switch, GPS location, battery volts and sends an SMS if in alarm.

It's design requirements are;

* Low power (20ma idle)
* Anchor / Mooring Alarm
* Battery monitoring (simple volts)
* Bilge switch monitoring
* Not designed to be on all the time (due to power)
* Use SMS as the lower common demoninator of coms
* Daily status messages

Logic summary
-------------

Basically it works thus;

0. Runs logrotate
1. Reads config
2. Starts a GPS thread logging GPS positions
3. Checks for inbound SMS messages from a 3G USB modem
4. Checks the anchor Alarm
5. Checks battery state
6. Checks a bilge switch
7. Checks to see if it needs to send a status SMS
8. Logs present status
9. Goes to sleep for a configurable time (rinse/repeate)


How it works
------------

* It is based on a Rasberry PI with a stripped down Rasbian image.
* Uses a PI Model A+ for size, cost and low power
* Uses an Adafruit Ultimate GPS connected to the PI reconfigured UART
* Uses a 3G USB modem to send/receive SMS messages
* Uses a mopi to sleep/wake, get battery Volts and have backup power
* Is mostly writen in Python with a bit of shell
* Uses GPIO pin 18 connected to a bilge switch and can alarm on that
* Puppet is used to configure the host, install all the needed packages and configure the services

Configuration
-------------

The Python script is configured in two ways;

1. By a confuration file `boatmon.config`
2. By sending the SMS number configuration messages

By far the easiest is config by SMS

### Config Script

The python script uses a config file called `boatmon.config` which looks like:
```[main]
[main]
debug = True
lat = 
lon = 
alarmrange = 0
phone = 01234567890
boatname = YourLovelyYachtName
dailystatus = 0700
lastdailystatuscheck = 2014-12-04 19:27:09.119902
wakeinnsecs = 120
batteryokmvolts = 1100
```

Note this config file also has state info in it.  Naughty I know.

### Config SMS

The system understands the following config SMS messages - if it does not understand you will either get a hint as a reply or no reply...

* `set boatname NAME` - Sets the boatname prefix to SMS messages
* `nupdate phone NUMBER` - Sets the phone number to send messages to
* `daily status TIMEUTC` - Sets a daily status SMS message 
* `daily status off` - Stops the daily status SMS messages
* `set anchor alarm DISTANCEINM` - Sets the anchor alarm (records the fix) and sets the distance given as the alarm range.  If no distance given defaults to 100M
* `anchor alarm off` - Stops the anchor alarm tracking / SMS messages
* `debug` - Enables Debuging (dev use only)
* `send state` - Will reply with a status SMS
* `set sleep time MINS` - Will set the time the Pi goes to sleep - suggest around 60 mins, cannot be less than 1 (minute)
* `set battery ok volts Mvolts` - Will set the milivolts at which the PI will report main battery OK or not
* `send instructions` - Sends a short instructions SMS (edited version of this)

## Install

* Assumes the PI has a network connection
* Assumes the GPS and 3G modem are connected/working 

```
sudo apt-get update
sudo apt-get upgrade
sudo raspi-config (make the SD card bigger) # you need the space!!!

reboot

git clone https://github.com/gregcope/piboatmon.git
sudo apt-get install puppet
cd piboatmon/manifests
sudo puppet apply init.pp --modulepath=/home/pi
sudo /etc/rc.local
```

Code to send SMS messages with AT commands;
http://www.cooking-hacks.com/documentation/tutorials/arduino-gprs-gsm-quadband-sim900

More AT examples in Python;
https://garretlabs.wordpress.com/2014/06/05/raspberry-and-the-remote-controlled-relay-a-low-level-approach-a-k-a-at-modem-commands-the-usual-suspects/

AT commands in detail
http://www.developershome.com/sms/cmgdCommand.asp
