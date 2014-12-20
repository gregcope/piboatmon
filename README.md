PiBoatMon
===

A system to turn a Raspberry PI into a low power boat monitoring solution.  It is configured by Puppet and then runs a Python script that checks the systems like Bilge Switch, GPS location, battery volts and sends an SMS if in alarm.

It's design requirements are;

* Low power (20ma idle)
* Anchor / Mooring Alarm
* Battery monitoring (volts)
* Bilge switch monitoring
* Not designed to be on all the time (due to power)
* Use SMS as the lower common demoninator of communication
* Daily status messages SMS messages

Logic summary
-------------

Basically it works thus;

0. Runs logrotate, gpsDate
1. Reads config
2. Wait till uptime is 55 secs as mopi will not shutdown 
3. Starts a GPS thread logging GPS positions
4. Checks for inbound SMS messages from a 3G USB modem
5. Checks the anchor Alarm
6. Checks battery state
7. Checks a bilge switch
8. Checks to see if it needs to send a status SMS
9. Logs present status
10. Waits till uptime is 60 secs (otherwise mopi will not shutdown)
11. Goes to sleep for a configurable time (rinse/repeate)

How it works
------------

* Uses a PI for size, cost and low power - in developement I use a Model B, so that I can ssh into it.  The production version is a Model A+
* Uses a stripped down Rasbian image
* Uses an [Adafruit Ultimate GPS](http://shop.pimoroni.com/products/adafruit-ultimate-gps-breakout) connected to the PI reconfigured UART
* Uses a 3G USB modem to send/receive SMS messages
* Uses a [mopi stackable](https://pi.gate.ac.uk/pages/mopi.html) to sleep/wake, get battery Volts and have backup power
* Uses Python with a bit of shell
* Uses GPIO pin 18 connected to a [bilge switch](http://www.ebay.co.uk/sch/i.html?_odkw=bilge+switch+seaflo&_from=R40%7CR40%7CR40&_osacat=0&_from=R40&_trksid=p2045573.m570.l1313.TR0.TRC0.H0.Xbilge+switch+seaflo+float&_nkw=bilge+switch+seaflo+float&_sacat=0) and can alarm on that
* Uses Puppet to configure the host, install all the needed packages and configure the services

Picture
-------
This is the developement board in the best tupperware I could find.  This is not supposed to be used on a boat for a few reasons.  Gives you an idea of parts etc...

![A raspberry PI in a tupperware box with a 3G modem, GPS and bilge switch connected](https://raw.githubusercontent.com/gregcope/piboatmon/master/mk1a-development.jpg "MK1a developement system")

Production Version
------------------

The production system is different and based on

* SIM900 Modem, smaller, better antenna
* Raspberry Pi A+, smaller, lower power
* External GPS antenna so that we get a better fix

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

* `setup` - Sets the registers phone, and ensures it can get a GPS fix
* `set boatname NAME` - Sets the boatname prefix to SMS messages
* `set phone NUMBER` - Sets the registered phone number to send messages to remeber to include the International STD code (ie +44 for UK)
* `set daily status TIMEUTC|off` - Sets/Disables a daily status SMS message 
* `set anchor alarm DISTANCEINM|off` - Sets/Disables the anchor alarm (records the fix) and sets the distance given as the alarm range.  If no distance given defaults to 100M
* `set debug on|off` - Enables|Disabled Debuging - basically lots of logging, however will also always send an SMS Status message when it runs
* `set regular status on|off` - Enables|Disables a regular status message each time it runs.  This can be a used as a regular running log when moving, if an anchor alarm has been set before departure. 
* `send state` - Will reply with a status SMS
* `set sleep time MINS` - Will set the time the Pi goes to sleep - suggest around 60 mins, cannot be less than 1 (minute)
* `set battery ok volts Mvolts` - Will set the milivolts at which the PI will report main battery OK or not
* `shutdown` - Will shutdown and never wake up.  Only from the registered phone.  Replies with an SMS.  Will need to be manually restarted.
* `send instructions` - Sends a short instructions SMS (edited version of this)

## Logging

* It will info log to `/home/pi/piboatmon/files/piboatmon.log`
* If debugging is on, it will log all sorts of usefull info
* Info logging just records changes of state

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
```

## Running it

* You must have run the install without any errors
* This is basically what will run at boot ...

`sudo /home/pi/files/piBoatMon.sh`

## FAQ

* **Can it do WIFI?**
No It is designed to be mostly off.  Might do another version with that
* **Can it alarm when the bilge switch goes off immediately?**
No as it might be alseep.  There is lots of logic complexity there (ie if on, what do you do when you've run and the switch is still high?
* **Can I run a bilge pump off the switch**
No as this is connected directly to the PI 5V - 12V would really upset it
* **Can it run a relay, to say run a bilge pump?**
Not in this version, but this should be easy to parse an SMS and put a relay on for X amount of time.

## Referances / Notes

Code to send SMS messages with AT commands;
http://www.cooking-hacks.com/documentation/tutorials/arduino-gprs-gsm-quadband-sim900

More AT examples in Python;
https://garretlabs.wordpress.com/2014/06/05/raspberry-and-the-remote-controlled-relay-a-low-level-approach-a-k-a-at-modem-commands-the-usual-suspects/

AT commands in detail
http://www.developershome.com/sms/cmgdCommand.asp
