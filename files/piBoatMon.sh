#!/bin/sh


timeOutSecs=90s
defaultSleepSecs=3600
logfile=/home/pi/piboatmon/files/piboatmon.log


# delete previous log file to stop it being added to
# need to remove the log file otherwise it gets recated each time!
/bin/rm $logfile

# try and set the date from GPS
/usr/bin/sudo /home/pi/piboatmon/files/gpsDate &

/usr/bin/logger -t piBoatMon "Setting the mopi power on timer to default of 3600 secs - piboatmon.py should overwrite it"
/usr/bin/sudo /usr/sbin/mopicli -won $defaultSleepSecs &

# unleash the python
/usr/bin/timeout $timeOutSecs /usr/bin/sudo /home/pi/piboatmon/files/piboatmon.py

# lame logrotate
# takes each copy and copies it into a logfile called piboatmon.log.20150106
# Copeied changed from here;
# http://unserializableone.blogspot.co.uk/2010/07/simple-bash-script-to-do-log-rotation.html
timestamp=`/bin/date +%Y%m%d`
newlogfile=$logfile.$timestamp
/bin/cat $logfile >> $newlogfile

# delete the oldest logfiles
/usr/bin/find /home/pi/piboatmon/files/  -name "piboatmon.log.*" -mtime +10 -exec rm {} \; &

/bin/sync &

sleep 30

/bin/sync

# force a nice power off in 1 sec
/usr/bin/sudo /usr/sbin/mopicli -wsd 1
