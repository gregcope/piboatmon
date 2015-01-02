# class to config ntp to prefer NMEA from GPS

class piboatmon::ntp {

# install packages
  package { 'ntp': }

# reconfig ntp to prefer NMEA GPS
# only if ntpd installed
# notify service
# edits from ideas here;
# http://www.catb.org/gpsd/gpsd-time-service-howto.html
  exec { 'configNtpGpsServer':
    logoutput => true,
    command => '/usr/bin/perl -p -i -e "s#server 127.127.28.0.*#server 127.127.28.0 minpoll 4 maxpoll 4 iburst prefer#" /etc/ntp.conf', 
    unless => '/bin/grep "server 127.127.28.0 minpoll 4 maxpoll 4 iburst prefer" /etc/ntp.conf',
  }

  exec { 'configNtpGpsFudge':
    logoutput => true,
    command => '/usr/bin/perl -p -i -e "s#fudge 127.127.28.0.*#fudge 127.127.28.0 time1 +0.340 refid GPS#" /etc/ntp.conf'
    unless => '/bin/grep "fudge 127.127.28.0 time1 \+0.340 refid GPS" /etc/ntp.conf',
  }

# ntp service
  service { 'ntp':
    require => [ Package [ 'ntp' ], Exec [ 'configNtp' ] ],
    ensure => running,
    enable => true,
  }
}
