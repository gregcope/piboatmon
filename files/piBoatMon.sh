#!/bin/sh


timeOutSecs=90s
defaultSleepSecs=3600

# try and set the date from GPS to kickoff ntpd
/usr/bin/logger -t piBoatMon "Starting gpsDate in the background"
/home/pi/piboatmon/files/gpsDate &

# log the ntp status
/usr/bin/logger -t piBoatMon ntpq status `/usr/bin/ntpq -p | grep NMEA`

# log the battery volts
/usr/bin/logger -t piBoatMon `/usr/bin/sudo /usr/sbin/mopicli -v1` &
/usr/bin/logger -t piBoatMon `/usr/bin/sudo /usr/sbin/mopicli -v2` &

/usr/bin/logger -t piBoatMon "Setting the mopi power on timer to default of 3600 secs - piboatmon.py should overwrite it"
/usr/bin/sudo /usr/sbin/mopicli -won $defaultSleepSecs &

/usr/bin/logger -t piBoatMon "Starting /home/pi/piboatmon/files/piboatmon.py"
# unleash the python
/usr/bin/timeout $timeOutSecs /usr/bin/sudo /home/pi/piboatmon/files/piboatmon.py
/usr/bin/logger -t piBoatMon "Finished /home/pi/piboatmon/files/piboatmon.py"

sleep 60

/usr/bin/logger -t piBoatMon "Going to sleep ... nite sync, mopciki -wsd 1"
/bin/sync

# force a nice power off in 1 sec
/usr/bin/sudo /usr/sbin/mopicli -wsd 1
