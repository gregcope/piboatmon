#!/bin/sh


/usr/bin/logger -t piBoatMon "About to run logrotate in the background"
# fire off logrotate manually
/usr/sbin/logrotate -f /etc/logrotate.conf &

/usr/bin/logger -t piBoatMon "Calling sync 3 times"
# start off old skhooollllll
/bin/sync; /bin/sync; /bin/sync

# log the ntp status
/usr/bin/logger -t piBoatMon ntpq status `/usr/bin/ntpq -p | grep NMEA`

# log the battery volts
/usr/bin/logger -t piBoatMon `/usr/bin/sudo /usr/sbin/mopicli -v1`
/usr/bin/logger -t piBoatMon `/usr/bin/sudo /usr/sbin/mopicli -v2`

/usr/bin/logger -t piBoatMon "Setting the mopi power on timer to default of 3600 secs (piboatmon.py should overwrite it"
/usr/bin/sudo /usr/sbin/mopicli -won 3600

/usr/bin/logger -t piBoatMon "Starting /home/pi/piboatmon/files/piboatmon.py"
# unleash the python
/usr/bin/timeout 90s /usr/bin/sudo /home/pi/piboatmon/files/piboatmon.py
/usr/bin/logger -t piBoatMon "Finished /home/pi/piboatmon/files/piboatmon.py"

/usr/bin/logger -t piBoatMon "Calling sync 3 times"
# oldskhol...
/bin/sync;/bin/sync;/bin/sync

sleep 60

# log the ntp status
/usr/bin/logger -t piBoatMon ntpq status `/usr/bin/ntpq -p | grep NMEA`

/usr/bin/logger -t piBoatMon "Going to sleep ... nite sync, mopciki -wsd 1"
/bin/sync

# force a nice power off in 1 sec
/usr/bin/sudo /usr/sbin/mopicli -wsd 1
