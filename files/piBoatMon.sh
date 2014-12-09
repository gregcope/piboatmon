#!/bin/sh

# start off old skhooollllll
/bin/sync; /bin/sync; /bin/sync

# unleash the python
/usr/bin/timeout 90s /usr/bin/sudo /home/pi/rpi/files/piboatmon.py

# oldskhol...
/bin/sync;/bin/sync;/bin/sync

sleep 360

# force a nice power off in 1 sec
/usr/bin/sudo /usr/sbin/mopicli -wsd 1
