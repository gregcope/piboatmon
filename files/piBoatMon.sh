#!/bin/sh


/usr/bin/logger -t piBoatMon "About to run logrotate in the background"
# fire off logrotate manually
/usr/sbin/logrotate -f /etc/logrotate.conf &

# set the date from GPS
GPSDATE=`/usr/bin/gpspipe -w | /usr/bin/head -10 | /bin/grep TPV | /bin/sed -r 's/.*"time":"([^"]*)".*/\1/' | /usr/bin/head -1`
/bin/date -s "$GPSDATE"
/usr/bin/logger -t piBoatMon "Setting date to: $GPSDATE"

/usr/bin/logger -t piBoatMon "Calling sync 3 times"
# start off old skhooollllll
/bin/sync; /bin/sync; /bin/sync

# log the battery volts
/usr/bin/logger -t piBoatMon `/usr/bin/sudo /usr/sbin/mopicli -v1`
/usr/bin/logger -t piBoatMon `/usr/bin/sudo /usr/sbin/mopicli -v2`

/usr/bin/logger -t piBoatMon "Starting /home/pi/piboatmon/files/piboatmon.py"
# unleash the python
/usr/bin/timeout 90s /usr/bin/sudo /home/pi/piboatmon/files/piboatmon.py
/usr/bin/logger -t piBoatMon "Finished /home/pi/piboatmon/files/piboatmon.py"

# log the battery volts
/usr/bin/logger -t piBoatMon `/usr/bin/sudo /usr/sbin/mopicli -v1`
/usr/bin/logger -t piBoatMon `/usr/bin/sudo /usr/sbin/mopicli -v2`

/usr/bin/logger -t piBoatMon "Calling sync 3 times"
# oldskhol...
/bin/sync;/bin/sync;/bin/sync

sleep 600

/usr/bin/logger -t piBoatMon "Going to sleep, sync"
/bin/sync

# force a nice power off in 1 sec
/usr/bin/sudo /usr/sbin/mopicli -wsd 1
