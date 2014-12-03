# class to install / configure gps on rpi UART port

class rpi::mopi {

# install some sensible packages
  package { 'simbamond': ensure => installed }

# fire up simbamond
  service { 'simbamond':
    ensure => running,
    hasstatus => true,
    hasrestart => true,
    require => Package['simbamond'],
  }

  file { '/etc/default/simbamond':
    owner => root,
    group => root,
    ensure => file,
    source => '/home/pi/rpi/manifests/simbamond',
  }
   # /bin/sed -n "/^# local config - DON'T/,/^# end of local config - DON'T/p" /etc/default/simbamond  | /bin/sed -n '2,$p' | /bin/sed '$d'
   # # wc1: -wc1 1 15000 12500 11000 11000
   # # wc2: -wc2 2 9600 7400 5200 4800
   # /usr/sbin/mopicli -wc2 2 9600 7400 5200 4800
   # /usr/sbin/mopicli -wc1 1 15000 12500 11000 11000
}
