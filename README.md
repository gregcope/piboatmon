PiBoatMon
===

A system to turn a Raspberry PI into a low power boat monitoring solution.  It is configured by Puppet and then runs a Python script that checks the systems like Bilge Switch, GPS location, battery volts and sends an SMS if in alarm.

Background
===

I want to know;

1. My boat is where I left it (anchor/morring)
2. It is not filling with water - aka afloat
3. The batteries are ok, and I have not left something on!
4. Not consume loads of power doing so

Design
===

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
2. Starts a GPS thread logging GPS positions
3. Wait till uptime is 55 secs as mopi will not shutdown
4. Checks for inbound SMS messages from a 3G USB modem
5. Checks the anchor Alarm
6. Checks battery state
7. Checks a bilge switch
8. Checks to see if it needs to send a status SMS
9. Logs present status and pings and https server the same info
10. Checks for a GPS fix, and stays awake for upto another 60 secs to get one
11. Waits till uptime is 60 secs (otherwise mopi will not shutdown)
12. Goes to sleep for a configurable time (rinse/repeate)

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

Bill Of Mattieals
"""

(Prices include UK VAT but not Shipping - YMMV)

Total around £160 ex Shipping.

* Mopi [Pimoroni £35](http://shop.pimoroni.com/products/mopi-mobile-pi-power)
* Adafruit Ultimate GPS [Pimoroni £34](http://shop.pimoroni.com/products/adafruit-ultimate-gps-breakout), [Amazon £33.99](http://www.amazon.co.uk/Adafruit-Ultimate-GPS-Breakout/dp/B00K9M6T8G/ref=sr_1_2?ie=UTF8&qid=1420205104&sr=8-2&keywords=adafr), [Pi Hut - Ebay £26.90](http://www.ebay.co.uk/itm/Adafruit-Ultimate-GPS-Breakout-/331200495869?pt=UK_Computing_Other_Computing_Networking&hash=item4d1d1680fd)
* Raspberry PI Model A+ [RS £18.61](http://uk.rs-online.com/web/p/processor-microcontroller-development-kits/8332699/), [Amazon £19.50](http://www.amazon.co.uk/Raspberry-Pi-Model-Plus-Motherboard/dp/B00Q8MM4PI/ref=sr_1_1?ie=UTF8&qid=1420206654&sr=8-1&keywords=raspberry+pi+a%2B), [Maplin £17.99] (http://www.maplin.co.uk/p/raspberry-pi-model-a-256-mb-mainboard-n03ea?gclid=COS-1fa59cICFWXHtAodwlYA1g), [Farnel £18.62](http://www.element14.com/community/docs/DOC-70725?CMP=KNC-PS-G-EU-SKU)
* 8GB Mini SD card [Various £4](https://www.google.co.uk/webhp?sourceid=chrome-instant&ion=1&espv=2&ie=UTF-8#q=8gb+micro+sd+card&tbm=shop) 
* GPS Attenna [Ebay £3.26](http://www.ebay.co.uk/itm/201082151408?_trksid=p2059210.m2749.l2649&ssPageName=STRK%3AMEBIDX%3AIT)
* HQRP UFL to SMA Connectors (need 2) [Pack Ebay £8.63] (http://www.ebay.co.uk/itm/390918412574?_trksid=p2059210.m2749.l2649&ssPageName=STRK%3AMEBIDX%3AIT)
* Female to Female Breadboard Jumper Cables - need 7 [Pack Amazon £1.25](http://www.amazon.co.uk/gp/product/B00D7SCMZ8?psc=1&redirect=true&ref_=oh_aui_detailpage_o01_s00)
* Secure Fix Direct Auto Float Switch (identical to Rule) [Amazon £8.95](http://www.amazon.co.uk/gp/product/B00KWW3490?psc=1&redirect=true&ref_=oh_aui_detailpage_o04_s00)
* Energizer 633287 9V Lithium Battery [Amazon £6.00](http://www.amazon.co.uk/gp/product/B003XM9YUO?psc=1&redirect=true&ref_=oh_aui_detailpage_o05_s00)
* One CR1220 3V Lithium GPS Battery [Pack Amazon £1.65](http://www.amazon.co.uk/gp/product/B003XM9YUO?psc=1&redirect=true&ref_=oh_aui_detailpage_o05_s00)
* USB to UART module [Ebay £1.19](http://www.ebay.co.uk/itm/271424127737?_trksid=p2059210.m2749.l2649&ssPageName=STRK%3AMEBIDX%3AIT)
* Two Waterproof Cable Glands 3-6.5mm [Pack Ebay £2.20](http://www.ebay.co.uk/itm/290996797625?_trksid=p2059210.m2749.l2649&ssPageName=STRK%3AMEBIDX%3AIT)
* Tinned Two Core 1.5mm2 Cable (5.7mm dia) for power supply / bilge extenion [30M Ebay £38](http://www.ebay.co.uk/itm/ROUND-TWIN-CABLE-1-5mm-21-AMP-2-x-21-0-30-TINNED-COPPER-2-CORE-MARINE-BOAT-WIRE-/360755968845?pt=UK_CarsParts_Vehicles_CarParts_SM&hash=item53febb3b4d)
* Wireless GSM or better Modem [SIM 900 Ebay £14.50](http://www.ebay.co.uk/itm/SIM900-GPRS-GSM-Shield-Development-Board-Module-For-Arduino-High-Quality/261718618344?_trksid=p2047675.c100011.m1850&_trkparms=aid%3D222007%26algo%3DSIC.MBE%26ao%3D1%26asc%3D28111%26meid%3Df961059f3c7f442dba43abaf584dbf13%26pid%3D100011%26prg%3D11472%26rk%3D1%26rkt%3D10%26sd%3D351270731630), [E160 Ebay £10 ish](http://www.ebay.co.uk/sch/i.html?_sacat=0&_nkw=e160+huawei&_frs=1)
* Solder assume you have ...
* Box - steal one from the kitchen - might use a Pelican later

Picture
-------
This is the developement board in the best tupperware I could find.  This is not supposed to be used on a boat for a few reasons.  Gives you an idea of parts etc...

![A raspberry PI in a tupperware box with a 3G modem, GPS and bilge switch connected](https://raw.githubusercontent.com/gregcope/piboatmon/master/mk1a-development.jpg "MK1a developement system")

Production Version
------------------

The production system is different and based on

* SIM800 or SIM900 or equiv Modem with a smaller, better antenna, as these are smaller, simpler (no usbswitch) and use less power
* Raspberry Pi A+, smaller, lower power
* External GPS antenna so that we can get a better fix

Configuration
-------------

The Python script is configured in two ways;

1. By a confuration file `boatmon.config`
2. By sending the SMS number configuration messages

By far the easiest is config by SMS.

### Config Script

The python script uses a config file called `boatmon.config` which looks like:
```
debug = False
wakeinnsecs = 900
sendstatus = False
dailystatus = 0800
lastdailystatuscheck = 2014-12-25 09:42:51.093899
alarmlat = 51.0138383332
alarmlon = -0.449643888667
alarmrange = 25
regularstatus = True
iteration = 34
lastruntime = 2014-12-25 18:59:32.612709
batteryokmvolts = 1100
phone = +44123456789
boatname = Regina
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
* `send config` - Sends the present config to registered phone

## Logging

* It will info log to `/home/pi/piboatmon/files/piboatmon.log`
* If debugging is on, it will log all sorts of usefull info
* Info logging just records changes of state

## Install

* Assumes the PI has a network connection
* Assumes the GPS and 3G modem are connected/working 

```
sudo apt-get update
sudo apt-get -y install puppet
cd /tmp
git clone https://github.com/gregcope/piboatmon.git
cd piboatmon/manifests
sudo puppet apply init.pp --modulepath=../..
sudo apt-get -y upgrade
sudo apt-get -y autoremove
sudo reboot
```

## Running it

* You must have run the install without any errors
* This is basically what will run at boot ...

`sudo sudo /home/pi/piboatmon/files/piboatmon.py`

* To check the logs as it runs you need to run the following *before*

`tail -f /home/pi/piboatmon/files/piboatmon.log &`

* If you want to emulate what will happen at boot run (it will shutdown!!!);

`sudo /home/pi/files/piBoatMon.sh`

## Upgrading

```
cd /tmp
git clone https://github.com/gregcope/piboatmon.git
cd piboatmon/manifests
sudo puppet apply init.pp --modulepath=../..
```

## FAQ

* **Can it do WIFI?**
No It is designed to be mostly off.  Might do another version with that.
* **Can it alarm when the bilge switch goes off immediately?**
No as it might be alseep.  There is lots of logic complexity there (ie if on, what do you do when you've run and the switch is still high?
* **Can I run a bilge pump off the switch?**
No as this is connected directly to the PI 3.3V rail.  12V would really upset it.
* **Can it run a relay, to say run a bilge pump?**
Not in this version, but this should be easy to parse an SMS and put a relay on for X amount of time.
* **Not getting any SMS messages?**
Do you have SMS credit?  Is the modem unlocked to your network, is it is working?
* **Not getting SMS messages, but had some before?** SMS Credit?  Battery power?  try sending `set debug on` or `set regular status on` to get SMS messages when ever it runs.  If you watch it run (ie you see the flashing LEDS), but no SMS, this is either an SMS/Modem fault or a code issue.
* **GPS criteria?** We need a GPS with an RTC Battery to enable fast fixes, otherwise it take most GPS units over a minute to fix... which is too long, as the code is running 25 secs afterboot, and then the logic takes only a few seconds, most of which is waiting on the modem.
* **GPS Accuracy?** Do you have an external SMA antenna fitted, does it have a good view of the sky?  Otherwise GPS accuracy is likely to be poor.
* **The SMS messages have the wrong time like 00:00:50?** The timezone is based on UTC, but if this is not a timezone issue, it is likely that the unit is not getting a GPS fix in time as it depends on this to set the time, as the RPI has no RTC.  Try texting `setup` to the unit to get GPS feedback.
* **What does BatX Missing mean?**  One of the batteries is either very dead, or disconnected.  If Bat2 then please replace the 9v reserve battery.
* **What is the number on the end of the each SMS?**  Each SMS ends with a number which is the number of runs that the system has done.  Hopefully this will get quite big!
* **Time is off by a few seconds** This does not do GPS leap second correction as this list needs updates.  However it does not need to be second perfect on timing.
* **Sent some SMS instructions, No response** Some Mobile providers offer poor service, and these may not be getting though (aka Giffgaff).  Consider switching!!!  Try sending a message from another phone (e.g. ```set phone NewPhoneNum``` and it should reply to both phones (you will need to set it back with ```set phone the_phone_num_you_used_before``` if you want your original.

## Referances / Notes

Code to send SMS messages with AT commands;
http://www.cooking-hacks.com/documentation/tutorials/arduino-gprs-gsm-quadband-sim900

More AT examples in Python;
https://garretlabs.wordpress.com/2014/06/05/raspberry-and-the-remote-controlled-relay-a-low-level-approach-a-k-a-at-modem-commands-the-usual-suspects/

AT commands in detail
http://www.developershome.com/sms/cmgdCommand.asp

PiMemspit
gpu_mem_256=112
in /boot/config.txt
http://www.raspberrypi.org/forums/viewtopic.php?p=223549#p223549

Modem Unlocking
---------------

To get an IMEI unlock code;
http://www.modemunlock.com/huawei.php

Instructions on how to check;
http://www.techmind.org/3Gmbb/index.html

Thoughts on UK Mobile Providers
-------------------------------

GiffGaff
+ Easy Setup
- Poor service (inbound SMS lost)

O2
+ Easy setup
- No simple PAYG SMS+Data product

Three
+ Appears to work
- Hard setup (lots of texts to deal with)
