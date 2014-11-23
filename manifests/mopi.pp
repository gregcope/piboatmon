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
  
}
