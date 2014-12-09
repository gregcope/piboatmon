# class to config ntp to prefer NMEA from GPS

class piboatmon::ntp {

# install packages
  package { 'ntp': }

# reconfig ntp to prefer NMEA GPS
# only if ntpd installed
# notify service
  exec { 'configNtp':
    logoutput => true,
    command => '/bin/echo -e "server 127.127.28.0 minpoll 4 prefer\nfudge 127.127.28.0 time1 +0.400 refid NMEA" >> /etc/ntp.conf',
    unless => '/bin/egrep "server 127.127.28.0 minpoll 4 prefer|fudge 127.127.28.0 time1 \+0.400 refid NMEA" /etc/ntp.conf',
    require => Package [ 'ntp' ],
    notify => Service [ 'ntp' ],
  }

# ntp service
  service { 'ntp':
    require => [ Package [ 'ntp' ], Exec [ 'configNtp' ] ],
    ensure => running,
  }
}
