#!/bin/sh

# unleash the python
/usr/bin/timeout -k 90s /usr/bin/sudo /home/pi/rpi/files/gpsThread.py

# force a nice power off
/usr/bin/sudo /usr/sbin/mopicli  -wsd 1
