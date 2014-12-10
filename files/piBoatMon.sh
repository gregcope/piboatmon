#!/bin/sh


/usr/bin/logger -t piBoatMon "About to run logrotate"
# fire off logrotate manually in background
/usr/sbin/logrotate -f /etc/logrotate.conf &

/usr/bin/logger -t piBoatMon "Calling sync 3 times"
# start off old skhooollllll
/bin/sync; /bin/sync; /bin/sync

/usr/bin/logger -t piBoatMon "Starting /home/pi/piboatmon/files/piboatmon.py"
# unleash the python
/usr/bin/timeout 90s /usr/bin/sudo /home/pi/piboatmon/files/piboatmon.py
/usr/bin/logger -t piBoatMon "Finished /home/pi/piboatmon/files/piboatmon.py"

/usr/bin/logger -t piBoatMon "Calling sync 3 times"
# oldskhol...
/bin/sync;/bin/sync;/bin/sync

sleep 600

/usr/bin/logger -t piBoatMon "Going to sleep, sync"
/bin/sync

# force a nice power off in 1 sec
/usr/bin/sudo /usr/sbin/mopicli -wsd 1
