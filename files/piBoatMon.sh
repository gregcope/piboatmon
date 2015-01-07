#!/bin/sh


timeOutSecs=90s
defaultSleepSecs=3600

/usr/bin/logger -t piBoatMon "Setting the mopi power on timer to default of 3600 secs - piboatmon.py should overwrite it"
/usr/bin/sudo /usr/sbin/mopicli -won $defaultSleepSecs &

# unleash the python
/usr/bin/timeout $timeOutSecs /usr/bin/sudo /home/pi/piboatmon/files/piboatmon.py

# lame logrotate
# takes each copy and copies it into a logfile called piboatmon.log.20150106
logfile=/home/pi/piboatmon/files/piboatmon.log
timestamp=`/bin/date +%Y%m%d`
newlogfile=$logfile.$timestamp
/bin/cat $logfile >> $newlogfile
# need to remove the log file otherwise it gets recated each time!
/bin/rm $logfile

# delete the oldest logfiles
/usr/bin/find /home/pi/piboatmon/files -name piboatmon.log*.tgz -mtime +10 -exec rm {} \;

sleep 60

/bin/sync

# force a nice power off in 1 sec
/usr/bin/sudo /usr/sbin/mopicli -wsd 1
